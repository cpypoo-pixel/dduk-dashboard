# -*- coding: utf-8 -*-
"""STEP 9: API 직접 호출로 내신 시험지(고등+중등) 약 1만건, 약 23만 문항 전체의
문항 목록과 쌍둥이/유사 문항 개수를 수집한다. 조회(GET)만 수행하며 어떤 데이터도 수정하지 않는다.
이미 열려 있는 인증된 CDP 브라우저 탭의 fetch()를 사용해 세션을 재사용한다.
중단 후 재실행 시 이미 완료된 시험지는 건너뛴다(이어서 진행)."""
import sys, json, csv, time
from pathlib import Path
sys.stdout.reconfigure(encoding="utf-8")
from playwright.sync_api import sync_playwright

BASE_DIR = Path(__file__).parent.parent
DATA_DIR = BASE_DIR / "data"
CDP_URL = "http://localhost:9333"
MATCH_FILE = DATA_DIR / "exam_match_result.json"
ITEMS_CSV = DATA_DIR / "step9_all_items.csv"
BOOKS_CSV = DATA_DIR / "step9_exam_summary.csv"
DONE_BOOKS_FILE = DATA_DIR / "step9_done_exams.txt"
ERROR_LOG = DATA_DIR / "step9_errors.log"
MAX_RUNTIME_SECONDS = 1800
CONCURRENCY = 15

ITEM_FIELDNAMES = [
    "book_id", "textbook_name", "sheet", "page", "item_num", "item_id",
    "item_kind_nm", "difficulty_nm", "is_review_status", "is_text_conversion_status",
    "del_yn", "upper1_taxo_nm", "upper2_taxo_nm", "upper3_taxo_nm", "taxo_nm",
    "last_review_complete_date", "twin_count", "similar_count", "other_relation_count",
    "collected_at",
]
BOOK_FIELDNAMES = [
    "book_id", "textbook_name", "sheet", "excel_item_count", "api_item_count",
    "is_review_complete", "review_done_count", "review_pending_count",
    "deleted_count", "twin_total", "similar_total", "status", "collected_at",
]

JS_BATCH = """
async ({bookId, itemIds, concurrency}) => {
  const out = [];
  const headers = { 'X-Requested-With': 'XMLHttpRequest' };
  let idx = 0;
  async function worker() {
    while (idx < itemIds.length) {
      const myIdx = idx++;
      const id = itemIds[myIdx];
      try {
        const res = await fetch(`/api/in/mnote-bank/book-item-edit/relation-list?book_id=${bookId}&item_id=${id}`, { headers });
        const j = await res.json();
        const rels = (j.data && j.data.relationList) ? j.data.relationList : [];
        let twin = 0, similar = 0, other = 0;
        for (const r of rels) {
          if (r.relation_nm === '쌍둥이') twin++;
          else if (r.relation_nm === '유사') similar++;
          else other++;
        }
        out[myIdx] = { item_id: id, twin, similar, other };
      } catch (e) {
        out[myIdx] = { item_id: id, error: String(e) };
      }
    }
  }
  const workers = [];
  for (let i = 0; i < concurrency; i++) workers.push(worker());
  await Promise.all(workers);
  return out;
}
"""


def log_error(msg):
    with open(ERROR_LOG, "a", encoding="utf-8") as f:
        f.write(f"{time.strftime('%Y-%m-%d %H:%M:%S')} {msg}\n")
    print(f"  [오류] {msg}", flush=True)


def load_done_books():
    if not DONE_BOOKS_FILE.exists():
        return set()
    return set(DONE_BOOKS_FILE.read_text(encoding="utf-8").splitlines())


def mark_book_done(book_id):
    with open(DONE_BOOKS_FILE, "a", encoding="utf-8") as f:
        f.write(f"{book_id}\n")


def ensure_csv_header(path, fieldnames):
    if not path.exists():
        with open(path, "w", newline="", encoding="utf-8-sig") as f:
            csv.DictWriter(f, fieldnames=fieldnames).writeheader()


def append_rows(path, fieldnames, rows):
    with open(path, "a", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        for r in rows:
            w.writerow(r)


def main():
    start_time = time.time()
    with open(MATCH_FILE, encoding="utf-8") as f:
        match = json.load(f)
    targets = match["matched"]
    print(f"[대상 시험지] {len(targets)}건", flush=True)

    ensure_csv_header(ITEMS_CSV, ITEM_FIELDNAMES)
    ensure_csv_header(BOOKS_CSV, BOOK_FIELDNAMES)
    done_books = load_done_books()
    print(f"[이미 완료된 시험지] {len(done_books)}건", flush=True)

    with sync_playwright() as p:
        browser = p.chromium.connect_over_cdp(CDP_URL)
        context = browser.contexts[0]
        target = None
        for pg in context.pages:
            if "book-item-edit" in pg.url:
                target = pg
        if target is None:
            print("[오류] book-item-edit 탭을 찾을 수 없습니다.", flush=True)
            return
        target.bring_to_front()

        processed_books = 0
        for t in targets:
            if time.time() - start_time > MAX_RUNTIME_SECONDS:
                print(f"[시간 제한 도달] {processed_books}권 처리 후 중단. 다시 실행하면 이어서 진행됩니다.", flush=True)
                break

            book_id = str(t["book_id"])
            if book_id in done_books:
                continue

            try:
                main_list = target.evaluate(
                    """
                    async (bookId) => {
                      const res = await fetch(`/api/in/mnote-bank/book-item-edit/main-list?perPage=&book_id=${bookId}&item_filter=&del_yn=N&page=1`,
                        { headers: { 'X-Requested-With': 'XMLHttpRequest' } });
                      const j = await res.json();
                      return j.data.contents;
                    }
                    """,
                    book_id,
                )
            except Exception as e:
                log_error(f"book_id={book_id} main-list 실패: {e}")
                continue

            item_ids = [c["item_id"] for c in main_list]
            try:
                rel_results = target.evaluate(
                    JS_BATCH,
                    {"bookId": book_id, "itemIds": item_ids, "concurrency": CONCURRENCY},
                )
            except Exception as e:
                log_error(f"book_id={book_id} relation-list 배치 실패: {e}")
                continue

            rel_by_id = {r["item_id"]: r for r in rel_results}
            now = time.strftime("%Y-%m-%d %H:%M:%S")

            item_rows = []
            review_done = review_pending = deleted = 0
            twin_total = similar_total = 0
            for c in main_list:
                rel = rel_by_id.get(c["item_id"], {})
                twin = rel.get("twin", 0) or 0
                similar = rel.get("similar", 0) or 0
                other = rel.get("other", 0) or 0
                twin_total += twin
                similar_total += similar
                if c.get("is_review_status") == "완료":
                    review_done += 1
                else:
                    review_pending += 1
                if c.get("del_yn") == "Y":
                    deleted += 1
                item_rows.append({
                    "book_id": book_id,
                    "textbook_name": t["name"],
                    "sheet": t["sheet"],
                    "page": c.get("book_page"),
                    "item_num": c.get("item_num"),
                    "item_id": c.get("item_id"),
                    "item_kind_nm": c.get("item_kind_nm"),
                    "difficulty_nm": c.get("difficulty_nm"),
                    "is_review_status": c.get("is_review_status"),
                    "is_text_conversion_status": c.get("is_text_conversion_status"),
                    "del_yn": c.get("del_yn"),
                    "upper1_taxo_nm": c.get("upper1_taxo_nm"),
                    "upper2_taxo_nm": c.get("upper2_taxo_nm"),
                    "upper3_taxo_nm": c.get("upper3_taxo_nm"),
                    "taxo_nm": c.get("taxo_nm"),
                    "last_review_complete_date": c.get("last_review_complete_date"),
                    "twin_count": twin,
                    "similar_count": similar,
                    "other_relation_count": other,
                    "collected_at": now,
                })

            append_rows(ITEMS_CSV, ITEM_FIELDNAMES, item_rows)
            append_rows(BOOKS_CSV, BOOK_FIELDNAMES, [{
                "book_id": book_id,
                "textbook_name": t["name"],
                "sheet": t["sheet"],
                "excel_item_count": t.get("excel_item_count"),
                "api_item_count": len(main_list),
                "is_review_complete": t.get("is_review_complete"),
                "review_done_count": review_done,
                "review_pending_count": review_pending,
                "deleted_count": deleted,
                "twin_total": twin_total,
                "similar_total": similar_total,
                "status": "ok",
                "collected_at": now,
            }])
            mark_book_done(book_id)
            processed_books += 1
            if processed_books % 10 == 0:
                elapsed = time.time() - start_time
                print(f"[진행] {processed_books}/{len(targets) - len(done_books)}권 처리 (경과 {elapsed:.0f}초)", flush=True)

        print(f"\n[이번 실행 요약] 신규처리={processed_books}권 소요시간={time.time()-start_time:.1f}초", flush=True)
        total_done = len(load_done_books())
        print(f"[누적 완료] {total_done} / {len(targets)}건", flush=True)
        if total_done >= len(targets):
            print("[완료] 전체 시험지 수집이 끝났습니다!", flush=True)
        else:
            print("[안내] 아직 끝나지 않았습니다. 다시 실행하면 이어서 진행됩니다.", flush=True)


if __name__ == "__main__":
    main()
