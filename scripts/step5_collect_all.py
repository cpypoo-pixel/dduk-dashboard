# STEP 5: 교재 전체 문항을 순회하며 상세 데이터를 수집한다.
# - 읽기(조회)만 수행, 검수 체크박스 변경이나 저장 버튼 클릭 없음
# - 중단 후 재실행 가능: 이미 수집된 문제코드는 건너뜀 (CSV에 즉시즉시 append)
# - 한 번 실행에 시간 제한(MAX_RUNTIME_SECONDS)을 둬서, 다 못 끝내면
#   안전하게 저장하고 종료 -> 다시 실행하면 이어서 진행됨
# - 문항 목록은 TOAST UI Grid의 가상 스크롤이라, 마우스 클릭 대신
#   키보드 방향키(ArrowDown)로 한 칸씩 이동하며 순회한다 (사람이 쓰는 방식과 동일)
import csv
import time
from datetime import datetime
from pathlib import Path
from playwright.sync_api import sync_playwright

BASE_DIR = Path(__file__).parent.parent
DATA_DIR = BASE_DIR / "data"
USER_DATA_DIR = BASE_DIR / ".browser_profile"
LOGIN_WAIT_SECONDS = 180
TEXTBOOK_NAME_EXACT = "중1 1학기 2022개정 수학 최상위수학 라이트"
TEXTBOOK_ID = "odapnote_최상위수학라이트_중1_1학기_2022개정"
OUT_CSV = DATA_DIR / "step5_all_items.csv"
ERROR_LOG = DATA_DIR / "step5_errors.log"
MAX_RUNTIME_SECONDS = 480  # 약 8분 - 10분 툴 제한 안에서 안전하게 종료하기 위함

FIELDNAMES = [
    "textbook_id", "textbook_name", "row_index", "page", "question_number",
    "question_code", "item_review_status", "text_conversion_status", "difficulty",
    "question_type", "deleted", "registered_by", "registered_at", "modified_by",
    "modified_at", "tabs_present", "tabs_count", "review_blocks_detail",
    "source", "collected_at", "status",
]

JS_CLICK_BY_TEXT = """
(targetText) => {
    const walker = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT);
    let node;
    while (node = walker.nextNode()) {
        if (node.textContent.trim() === targetText) {
            let el = node.parentElement;
            let cur = el;
            for (let i = 0; i < 6 && cur; i++) {
                if (cur.tagName === 'A' || cur.tagName === 'BUTTON' || cur.onclick || cur.getAttribute('role') === 'button') {
                    cur.click();
                    return 'clicked:' + cur.tagName;
                }
                cur = cur.parentElement;
            }
            el.click();
            return 'clicked-fallback-leaf';
        }
    }
    return 'not-found';
}
"""

JS_EXTRACT_REVIEW_BLOCKS = """
() => {
    const results = [];
    const walker = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT);
    let node;
    while (node = walker.nextNode()) {
        if (node.textContent.trim() === '검수완료') {
            let labelEl = node.parentElement;
            let container = labelEl.closest('div');
            let checkbox = container ? container.querySelector('input[type=checkbox]') : null;
            if (!checkbox && container && container.parentElement) {
                checkbox = container.parentElement.querySelector('input[type=checkbox]');
            }
            let row = labelEl.closest('tr');
            let blockLabel = '';
            if (row) {
                const firstCell = row.querySelector('td, th');
                if (firstCell) blockLabel = firstCell.textContent.trim().slice(0, 20);
            }
            results.push({ blockLabel, checked: checkbox ? checkbox.checked : null });
        }
    }
    return results;
}
"""


def shot(page, name):
    path = DATA_DIR / f"{name}.png"
    try:
        page.screenshot(path=str(path))
        print(f"[스크린샷] {path}", flush=True)
    except Exception as e:
        print(f"[스크린샷 실패:{name}] {e}", flush=True)


def extract_field(page, label):
    try:
        candidates = page.get_by_text(label, exact=True).all()
    except Exception:
        return None
    for cand in candidates:
        try:
            if not cand.is_visible():
                continue
            box = cand.bounding_box()
            if not box:
                continue
            if box["x"] < 1330 or box["y"] < 150 or box["y"] > 950 or box["x"] > 1600:
                continue
            is_grid = cand.evaluate(
                "el => { let c = el; for (let i=0;i<8 && c;i++){ if (c.className && typeof c.className==='string' && c.className.includes('tui-grid')) return true; c = c.parentElement; } return false; }"
            )
            if is_grid:
                continue
            row = cand.locator("xpath=ancestor::tr[1]")
            if row.count() == 0:
                row = cand.locator("xpath=..")
            sel = row.locator("select")
            if sel.count() > 0:
                try:
                    opt_text = sel.first.locator("option:checked").inner_text(timeout=500)
                    if opt_text:
                        return opt_text.strip()
                except Exception:
                    pass
            inp = row.locator("input[type=text], input:not([type])")
            if inp.count() > 0:
                try:
                    val = inp.first.input_value(timeout=500)
                    if val:
                        return val
                except Exception:
                    pass
            radios = row.locator("input[type=radio]")
            rcount = radios.count()
            if rcount > 0:
                try:
                    for ri in range(rcount):
                        r = radios.nth(ri)
                        if r.evaluate("el => el.checked"):
                            rid = r.get_attribute("id") or ""
                            val = r.get_attribute("value") or ""
                            lbl = row.locator(f"label[for='{rid}']") if rid else None
                            if lbl is not None and lbl.count() > 0:
                                return lbl.first.inner_text(timeout=500).strip()
                            if val:
                                return val
                except Exception:
                    pass
            text = row.inner_text(timeout=500)
            text = text.replace(label, "", 1).strip()
            if len(text) < 200:
                return text[:100]
        except Exception:
            continue
    return None


def load_done_keys():
    """이미 수집된 (page, question_number) 키 집합을 CSV에서 읽어온다."""
    done = set()
    if OUT_CSV.exists():
        with open(OUT_CSV, "r", encoding="utf-8-sig", newline="") as f:
            reader = csv.DictReader(f)
            for row in reader:
                key = (row.get("page"), row.get("question_number"))
                if key != (None, None):
                    done.add(key)
    return done


def append_row(row):
    is_new = not OUT_CSV.exists()
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    with open(OUT_CSV, "a", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
        if is_new:
            writer.writeheader()
        writer.writerow(row)


def log_error(idx, msg):
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    with open(ERROR_LOG, "a", encoding="utf-8") as f:
        f.write(f"{datetime.now().isoformat()} idx={idx} {msg}\n")


start_time = time.monotonic()
done_keys = load_done_keys()
print(f"[재시작 확인] 기존에 수집된 문항 수: {len(done_keys)}", flush=True)

with sync_playwright() as p:
    context = p.chromium.launch_persistent_context(
        str(USER_DATA_DIR), headless=False, viewport={"width": 1600, "height": 1000},
    )
    for p_old in list(context.pages)[1:]:
        try:
            p_old.close()
        except Exception:
            pass
    page = context.pages[0] if context.pages else context.new_page()

    page.goto("https://adm.mswitch.co.kr/", timeout=20000, wait_until="networkidle")
    print(f"[안내] 로그인 확인 중... URL={page.url}", flush=True)
    if "/login" in page.url:
        print(f"[대기] {LOGIN_WAIT_SECONDS}초 동안 로그인해 주세요.", flush=True)
        page.wait_for_timeout(LOGIN_WAIT_SECONDS * 1000)
        page.goto("https://adm.mswitch.co.kr/", timeout=20000, wait_until="networkidle")
    page.wait_for_timeout(1000)
    if "/login" in page.url:
        print("[중단] 로그인되지 않았습니다.", flush=True)
        shot(page, "s5_01_login_failed")
        context.close()
        raise SystemExit(0)
    print(f"[로그인 확인] URL={page.url}", flush=True)

    pages_before = len(context.pages)
    mnote_page = None
    for attempt in range(1, 9):
        print(f"[시도 {attempt}/8] 그리드 메뉴 + 엠노트 클릭", flush=True)
        try:
            page.keyboard.press("Escape")
        except Exception:
            pass
        page.wait_for_timeout(300)
        opened = False
        try:
            grid_el = page.get_by_text("전체서비스", exact=True).first
            if grid_el.count() > 0:
                grid_el.click(timeout=2000, force=True)
                opened = True
        except Exception:
            pass
        if not opened:
            page.mouse.click(1524, 24)
        page.wait_for_timeout(700)
        try:
            result = page.evaluate(JS_CLICK_BY_TEXT, "엠노트")
            print(f"  결과: {result}", flush=True)
        except Exception as e:
            print(f"  예외: {e}", flush=True)
        page.wait_for_timeout(2000)
        if len(context.pages) > pages_before:
            mnote_page = context.pages[-1]
            break
        print("  새 탭 없음, 재시도", flush=True)

    if mnote_page is None:
        print("[중단] 엠노트 진입 실패", flush=True)
        shot(page, "s5_02_mnote_fail")
        context.close()
        raise SystemExit(0)

    mnote_page.wait_for_load_state("networkidle", timeout=15000)
    print(f"[엠노트 진입 성공] {mnote_page.url}", flush=True)

    print("[STEP] 좌측 드롭다운 -> 교재등록", flush=True)
    try:
        mnote_page.get_by_text("오답노트", exact=True).first.click(timeout=8000)
        mnote_page.wait_for_timeout(800)
    except Exception as e:
        print(f"[드롭다운 클릭 실패] {e}", flush=True)
        shot(mnote_page, "s5_03_dropdown_fail")
        context.close()
        raise SystemExit(0)

    booklist_page = mnote_page
    booklist_ok = False
    for attempt in range(1, 6):
        try:
            pages_before2 = len(context.pages)
            target = mnote_page.get_by_text("교재등록", exact=True).first
            if not target.is_visible():
                print(f"  [시도 {attempt}/5] 드롭다운 다시 열기", flush=True)
                mnote_page.get_by_text("오답노트", exact=True).first.click(timeout=5000, force=True)
                mnote_page.wait_for_timeout(600)
            target.click(timeout=5000, force=True)
            mnote_page.wait_for_timeout(1500)
            if len(context.pages) > pages_before2:
                booklist_page = context.pages[-1]
                booklist_page.wait_for_load_state("networkidle", timeout=15000)
            elif "/booklist" in mnote_page.url:
                booklist_page = mnote_page
            else:
                continue
            print(f"[교재등록 URL] {booklist_page.url}", flush=True)
            booklist_ok = True
            break
        except Exception as e:
            print(f"  [시도 {attempt}/5 실패] {e}", flush=True)
            mnote_page.wait_for_timeout(500)

    if not booklist_ok:
        print("[중단] 교재등록 진입 실패", flush=True)
        shot(mnote_page, "s5_04_booklist_fail")
        context.close()
        raise SystemExit(0)

    print("[STEP] 첫 번째 행 체크박스 선택", flush=True)
    try:
        first_checkbox = booklist_page.locator("table tbody input[type=checkbox]").first
        try:
            first_checkbox.check(timeout=3000, force=True)
        except Exception:
            first_checkbox.evaluate(
                """(el) => {
                    el.checked = true;
                    el.dispatchEvent(new Event('change', { bubbles: true }));
                    el.dispatchEvent(new Event('click', { bubbles: true }));
                }"""
            )
        booklist_page.wait_for_timeout(500)
    except Exception as e:
        print(f"[체크박스 선택 실패] {e}", flush=True)
        shot(booklist_page, "s5_06_checkbox_fail")
        context.close()
        raise SystemExit(0)

    print("[STEP] 문제편집기 버튼 클릭", flush=True)
    editor_page = booklist_page
    try:
        pages_before3 = len(context.pages)
        booklist_page.get_by_text("문제편집기", exact=True).first.click(timeout=8000, force=True)
        booklist_page.wait_for_timeout(2000)
        if len(context.pages) > pages_before3:
            editor_page = context.pages[-1]
            editor_page.wait_for_load_state("networkidle", timeout=15000)
        print(f"[문제편집기 진입] URL={editor_page.url}", flush=True)
    except Exception as e:
        print(f"[문제편집기 진입 실패] {e}", flush=True)
        shot(booklist_page, "s5_07_editor_fail")
        context.close()
        raise SystemExit(0)

    print(f"[STEP] 편집기 내 교재 검색: {TEXTBOOK_NAME_EXACT}", flush=True)
    try:
        inner_search = editor_page.get_by_placeholder("교재/내신명을 입력해주세요")
        inner_search.click(timeout=5000, force=True)
        inner_search.fill("", force=True)
        editor_page.keyboard.type(TEXTBOOK_NAME_EXACT, delay=120)
        editor_page.wait_for_timeout(1500)
        option = editor_page.get_by_text(TEXTBOOK_NAME_EXACT, exact=False).first
        option.wait_for(timeout=5000)
        option.click(timeout=5000, force=True)
        editor_page.wait_for_timeout(1000)
        editor_page.mouse.click(835, 70)
        editor_page.wait_for_timeout(2000)

        total_text = editor_page.locator("#grid_main_tot_cnt").inner_text(timeout=3000)
        total_count = int(total_text.strip())
        print(f"[문제 목록] 총 {total_count}건", flush=True)
    except Exception as e:
        print(f"[교재 검색 실패] {e}", flush=True)
        shot(editor_page, "s5_10_search_fail")
        context.close()
        raise SystemExit(0)

    # 첫 행 클릭해서 그리드에 포커스
    try:
        editor_page.locator("table tbody tr").nth(1).click(timeout=5000, force=True)
        editor_page.wait_for_timeout(800)
    except Exception as e:
        print(f"[첫 행 포커스 실패] {e}", flush=True)
        shot(editor_page, "s5_11_focus_fail")
        context.close()
        raise SystemExit(0)

    collected_count = 0
    skipped_count = 0
    error_count = 0
    prev_code = None

    for idx in range(total_count):
        if time.monotonic() - start_time > MAX_RUNTIME_SECONDS:
            print(f"[시간 제한 도달] {idx}번째에서 중단. 다시 실행하면 이어서 진행됩니다.", flush=True)
            break

        if idx > 0:
            try:
                editor_page.keyboard.press("ArrowDown")
            except Exception as e:
                log_error(idx, f"ArrowDown 실패: {e}")

        # 빠른 스킵 판단: 먼저 page/문제번호만 확인해서 이미 수집했는지 체크
        page_no = None
        q_no = None
        try:
            pc = editor_page.locator(f"[data-row-key='{idx}'][data-column-name='book_page']")
            if pc.count() > 0:
                page_no = pc.first.inner_text(timeout=800).strip()
            inc = editor_page.locator(f"[data-row-key='{idx}'][data-column-name='item_num']")
            if inc.count() > 0:
                q_no = inc.first.inner_text(timeout=800).strip()
        except Exception:
            pass

        if (page_no, q_no) in done_keys:
            skipped_count += 1
            continue

        try:
            q_code = extract_field(editor_page, "문제코드")
            for _ in range(6):
                if q_code and q_code != prev_code:
                    break
                editor_page.wait_for_timeout(400)
                q_code = extract_field(editor_page, "문제코드")

            item_review = extract_field(editor_page, "문항검수")
            text_conv = extract_field(editor_page, "텍스트변환")
            difficulty = extract_field(editor_page, "문제난이도")
            q_type = extract_field(editor_page, "문제종류")
            reg_user = extract_field(editor_page, "등록자")
            reg_at = extract_field(editor_page, "등록일시")
            mod_user = extract_field(editor_page, "수정자")
            mod_at = extract_field(editor_page, "수정일시")
            deleted = extract_field(editor_page, "문제삭제여부")

            tabs = []
            tab_candidates = editor_page.locator(
                "text=/^(원문항|쌍둥이\\s*\\d*번?|유사\\s*\\d*번?)$/"
            ).all()
            for t in tab_candidates:
                try:
                    txt = t.inner_text(timeout=200).strip()
                    if txt and txt not in tabs:
                        tabs.append(txt)
                except Exception:
                    pass

            review_blocks = []
            try:
                review_blocks = editor_page.evaluate(JS_EXTRACT_REVIEW_BLOCKS)
            except Exception:
                pass

            status = "ok"
            if q_code == prev_code:
                status = "stale_warning"
            prev_code = q_code

            row = {
                "textbook_id": TEXTBOOK_ID,
                "textbook_name": TEXTBOOK_NAME_EXACT,
                "row_index": idx,
                "page": page_no,
                "question_number": q_no,
                "question_code": q_code,
                "item_review_status": item_review,
                "text_conversion_status": text_conv,
                "difficulty": difficulty,
                "question_type": q_type,
                "deleted": deleted,
                "registered_by": reg_user,
                "registered_at": reg_at,
                "modified_by": mod_user,
                "modified_at": mod_at,
                "tabs_present": "|".join(tabs),
                "tabs_count": len(tabs),
                "review_blocks_detail": str(review_blocks),
                "source": "browser_automation",
                "collected_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "status": status,
            }
            append_row(row)
            done_keys.add((page_no, q_no))
            collected_count += 1

            if collected_count % 25 == 0:
                print(f"[진행] {collected_count}건 수집 완료 (스킵 {skipped_count}, 오류 {error_count}) idx={idx}/{total_count}", flush=True)

        except Exception as e:
            error_count += 1
            log_error(idx, str(e))
            print(f"  [오류] idx={idx}: {e}", flush=True)
            continue

    elapsed = time.monotonic() - start_time
    print(f"\n[이번 실행 요약] 신규수집={collected_count} 스킵(이미수집됨)={skipped_count} 오류={error_count} 소요시간={elapsed:.1f}초", flush=True)
    print(f"[누적 수집] {len(done_keys)} / {total_count}건", flush=True)
    if len(done_keys) < total_count:
        print("[안내] 아직 전체 수집이 끝나지 않았습니다. 이 스크립트를 다시 실행하면 이어서 진행됩니다.", flush=True)
    else:
        print("[완료] 전체 문항 수집이 끝났습니다!", flush=True)

    context.close()

print("[종료]", flush=True)
