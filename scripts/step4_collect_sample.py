# STEP 4: 검증된 흐름(로그인->엠노트->교재등록->문제편집기->교재검색)을 재사용해
# 문항 5개의 상세 데이터(검수상태, 쌍둥이 탭 등)를 수집해 CSV로 저장한다.
# 읽기(조회)만 수행하며, 검수 체크박스를 변경하거나 저장 버튼을 누르지 않는다.
import csv
from datetime import datetime
from pathlib import Path
from playwright.sync_api import sync_playwright

BASE_DIR = Path(__file__).parent.parent
DATA_DIR = BASE_DIR / "data"
USER_DATA_DIR = BASE_DIR / ".browser_profile"
LOGIN_WAIT_SECONDS = 180
TEXTBOOK_NAME_EXACT = "중1 1학기 2022개정 수학 최상위수학 라이트"
TEXTBOOK_ID = "odapnote_최상위수학라이트_중1_1학기_2022개정"
SAMPLE_SIZE = 5
OUT_CSV = DATA_DIR / "step4_sample_items.csv"

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
    """실제 화면의 우측 상세패널에 있는 매칭만 사용.
    TOAST UI Grid(tui-grid)가 문제 목록 표를 가상 렌더링하면서 같은 라벨 텍스트를 가진
    숨은/스크롤 밖 헤더 셀을 만들어내므로, 'tui-grid' 클래스를 가진 조상은 전부 제외한다."""
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
            # 우측 상세패널 영역(x>1330, y 150~950)만 인정 - 상단 필터바/좌측 목록/하단 그룹문제 표 제외
            if box["x"] < 1330 or box["y"] < 150 or box["y"] > 950 or box["x"] > 1600:
                continue

            is_grid = cand.evaluate(
                "el => { let c = el; for (let i=0;i<8 && c;i++){ if (c.className && typeof c.className==='string' && c.className.includes('tui-grid')) return true; c = c.parentElement; } return false; }"
            )
            if is_grid:
                continue  # TUI Grid의 가상 컬럼 헤더(실제 안 보임) 제외

            row = cand.locator("xpath=ancestor::tr[1]")
            if row.count() == 0:
                row = cand.locator("xpath=..")

            # select가 있으면 선택된 "표시 텍스트"를 우선 사용 (예: 문제난이도='중하', 문제종류='선다형')
            sel = row.locator("select")
            if sel.count() > 0:
                try:
                    opt_text = sel.first.locator("option:checked").inner_text(timeout=500)
                    if opt_text:
                        return opt_text.strip()
                except Exception:
                    pass

            # input(읽기전용 값) - 예: 문제코드
            inp = row.locator("input[type=text], input:not([type])")
            if inp.count() > 0:
                try:
                    val = inp.first.input_value(timeout=500)
                    if val:
                        return val
                except Exception:
                    pass

            # 라디오 버튼 (예: 문제삭제여부 Y/N) - :checked 셀렉터 대신 JS로 직접 checked 속성 확인
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
        shot(page, "s4_01_login_failed")
        context.close()
        raise SystemExit(0)
    print(f"[로그인 확인] URL={page.url}", flush=True)

    # 엠노트 진입 (최대 8회 재시도)
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
        shot(page, "s4_02_mnote_fail")
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
        shot(mnote_page, "s4_03_dropdown_fail")
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
                print(f"  [시도 {attempt}/5] URL 변화 없음, 재시도", flush=True)
                continue
            print(f"[교재등록 URL] {booklist_page.url}", flush=True)
            booklist_ok = True
            break
        except Exception as e:
            print(f"  [시도 {attempt}/5 실패] {e}", flush=True)
            mnote_page.wait_for_timeout(500)

    if not booklist_ok:
        print("[중단] 교재등록 진입 실패 (5회 시도)", flush=True)
        shot(mnote_page, "s4_04_booklist_fail")
        context.close()
        raise SystemExit(0)

    print("[STEP] 첫 번째 행 체크박스 선택 (버튼 활성화 목적)", flush=True)
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
        shot(booklist_page, "s4_06_checkbox_fail")
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
        shot(booklist_page, "s4_07_editor_fail")
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

        total = editor_page.get_by_text("문제 목록").first.locator("xpath=..").inner_text(timeout=2000)
        print(f"[문제 목록] {total}", flush=True)
        shot(editor_page, "s4_10_loaded")
    except Exception as e:
        print(f"[교재 검색 실패] {e}", flush=True)
        shot(editor_page, "s4_10_search_fail")
        context.close()
        raise SystemExit(0)

    # ---- STEP 4 핵심: 문항 5개 순회하며 상세 데이터 수집 ----
    print(f"[STEP] 문항 {SAMPLE_SIZE}개 상세 데이터 수집 시작", flush=True)
    collected_rows = []
    collected_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    try:
        row_locators = editor_page.locator("table tbody tr").all()[:SAMPLE_SIZE]
        print(f"[좌측 목록에서 찾은 행 수] {len(row_locators)}", flush=True)
    except Exception as e:
        print(f"[좌측 목록 조회 실패] {e}", flush=True)
        row_locators = []

    prev_code = None
    for idx in range(len(row_locators)):
        print(f"[문항 {idx + 1}/{len(row_locators)}] 클릭", flush=True)
        try:
            row = editor_page.locator("table tbody tr").nth(idx)
            row.click(timeout=5000, force=True)
        except Exception as e:
            print(f"  [클릭 실패] {e}", flush=True)
            continue

        # 상세 패널이 실제로 갱신될 때까지 폴링 (문제코드가 바뀔 때까지, 최대 ~4초)
        # 그래도 안 바뀌면 행을 한 번 더 클릭해서 재시도
        q_code = extract_field(editor_page, "문제코드")
        for retry_round in range(2):
            for _ in range(8):
                if q_code and (idx == 0 or q_code != prev_code):
                    break
                editor_page.wait_for_timeout(500)
                q_code = extract_field(editor_page, "문제코드")
            if q_code and (idx == 0 or q_code != prev_code):
                break
            if retry_round == 0:
                print("  [재클릭 시도] 상세 패널이 갱신되지 않아 다시 클릭", flush=True)
                try:
                    row.click(timeout=5000, force=True)
                except Exception:
                    pass
                editor_page.wait_for_timeout(800)
                q_code = extract_field(editor_page, "문제코드")
        if q_code == prev_code and idx != 0:
            print(f"  [경고] 문제코드가 이전과 동일함({q_code}) - 갱신 실패 가능성", flush=True)
        prev_code = q_code

        page_no = None
        q_no = None
        try:
            # TUI Grid는 체크박스/No. 칼럼(L-side, frozen)과 나머지 데이터 칼럼(R-side)을
            # 별도의 <table>로 렌더링한다. data-row-key로 두 쪽을 연결해 R-side 값을 읽는다.
            pc = editor_page.locator(f"[data-row-key='{idx}'][data-column-name='book_page']")
            if pc.count() > 0:
                page_no = pc.first.inner_text(timeout=500).strip()
            inc = editor_page.locator(f"[data-row-key='{idx}'][data-column-name='item_num']")
            if inc.count() > 0:
                q_no = inc.first.inner_text(timeout=500).strip()
        except Exception:
            pass
        item_review = extract_field(editor_page, "문항검수")
        text_conv = extract_field(editor_page, "텍스트변환")
        difficulty = extract_field(editor_page, "문제난이도")
        q_type = extract_field(editor_page, "문제종류")
        reg_user = extract_field(editor_page, "등록자")
        reg_at = extract_field(editor_page, "등록일시")
        mod_user = extract_field(editor_page, "수정자")
        mod_at = extract_field(editor_page, "수정일시")
        deleted = extract_field(editor_page, "문제삭제여부")

        # 탭 목록 (원문항/쌍둥이N번/유사N번)
        tabs = []
        try:
            for tab_loc in editor_page.get_by_text("원문항", exact=False).all()[:1]:
                pass
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
        except Exception as e:
            print(f"  [탭 목록 추출 실패] {e}", flush=True)

        # 문제/정답/해설 개별 검수완료 상태
        review_blocks = []
        try:
            review_blocks = editor_page.evaluate(JS_EXTRACT_REVIEW_BLOCKS)
        except Exception as e:
            print(f"  [세부 검수 상태 추출 실패] {e}", flush=True)

        print(f"  페이지={page_no} 문제번호={q_no} 문제코드={q_code} 문항검수={item_review}", flush=True)
        print(f"  텍스트변환={text_conv} 난이도={difficulty} 종류={q_type} 삭제={deleted}", flush=True)
        print(f"  탭목록={tabs}", flush=True)
        print(f"  세부검수={review_blocks}", flush=True)

        collected_rows.append({
            "textbook_id": TEXTBOOK_ID,
            "textbook_name": TEXTBOOK_NAME_EXACT,
            "sample_index": idx + 1,
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
            "collected_at": collected_at,
        })

        shot(editor_page, f"s4_item{idx + 1}")

    # CSV 저장
    if collected_rows:
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        with open(OUT_CSV, "w", newline="", encoding="utf-8-sig") as f:
            writer = csv.DictWriter(f, fieldnames=list(collected_rows[0].keys()))
            writer.writeheader()
            writer.writerows(collected_rows)
        print(f"[CSV 저장 완료] {OUT_CSV} ({len(collected_rows)}행)", flush=True)
    else:
        print("[경고] 수집된 행이 없습니다.", flush=True)

    print("[완료] STEP 4 수집 성공", flush=True)
    context.close()

print("[종료]", flush=True)
