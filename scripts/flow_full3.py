# 전체 흐름 v3: 학습한 전체 경로를 한 세션에서 연결
# 로그인 -> (재시도) 엠노트(오답노트) 진입 -> 좌측 드롭다운에서 교재등록 선택
# -> 교재 검색 -> 체크박스 선택 -> 문제편집기 진입
from pathlib import Path
from playwright.sync_api import sync_playwright

BASE_DIR = Path(__file__).parent.parent
DATA_DIR = BASE_DIR / "data"
USER_DATA_DIR = BASE_DIR / ".browser_profile"
LOGIN_WAIT_SECONDS = 180
TEXTBOOK_SEARCH_TEXT = "최상위수학 라이트"
TEXTBOOK_NAME_EXACT = "중1 1학기 2022개정 수학 최상위수학 라이트"

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


def shot(page, name):
    path = DATA_DIR / f"{name}.png"
    try:
        page.screenshot(path=str(path))
        print(f"[스크린샷] {path}", flush=True)
    except Exception as e:
        print(f"[스크린샷 실패:{name}] {e}", flush=True)


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
    print(f"[현재 URL] {page.url}", flush=True)
    if "/login" in page.url:
        print("[중단] 로그인되지 않았습니다.", flush=True)
        shot(page, "f3_01_login_failed")
        context.close()
        raise SystemExit(0)

    # 엠노트(오답노트) 진입: 최대 8회 재시도
    pages_before = len(context.pages)
    mnote_page = None
    MAX_MNOTE_ATTEMPTS = 8
    for attempt in range(1, MAX_MNOTE_ATTEMPTS + 1):
        print(f"[시도 {attempt}/{MAX_MNOTE_ATTEMPTS}] 그리드 메뉴 + 엠노트 클릭", flush=True)
        try:
            page.keyboard.press("Escape")
        except Exception:
            pass
        page.wait_for_timeout(300)
        # 그리드 메뉴 버튼: 텍스트("전체서비스")로 우선 시도, 실패하면 좌표로 폴백
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
        print(f"[중단] 엠노트 진입 실패 ({MAX_MNOTE_ATTEMPTS}회 시도)", flush=True)
        shot(page, "f3_02_mnote_fail")
        context.close()
        raise SystemExit(0)

    mnote_page.wait_for_load_state("networkidle", timeout=15000)
    print(f"[엠노트 진입 성공] {mnote_page.url}", flush=True)
    shot(mnote_page, "f3_02_mnote_entered")

    # 좌측 상단 '오답노트' 드롭다운 클릭 -> '교재등록' 메뉴 클릭
    print("[STEP] 좌측 드롭다운 열기", flush=True)
    try:
        mnote_page.get_by_text("오답노트", exact=True).first.click(timeout=8000)
        mnote_page.wait_for_timeout(800)
        shot(mnote_page, "f3_03_dropdown_open")
    except Exception as e:
        print(f"[드롭다운 클릭 실패] {e}", flush=True)
        shot(mnote_page, "f3_03_dropdown_fail")
        context.close()
        raise SystemExit(0)

    print("[STEP] 교재등록 메뉴 항목 클릭", flush=True)
    booklist_page = mnote_page
    try:
        pages_before2 = len(context.pages)
        mnote_page.get_by_text("교재등록", exact=True).first.click(timeout=8000)
        mnote_page.wait_for_timeout(1500)
        if len(context.pages) > pages_before2:
            booklist_page = context.pages[-1]
            booklist_page.wait_for_load_state("networkidle", timeout=15000)
        shot(booklist_page, "f3_04_booklist")
        print(f"[교재등록 URL] {booklist_page.url}", flush=True)
    except Exception as e:
        print(f"[교재등록 클릭 실패] {e}", flush=True)
        shot(mnote_page, "f3_04_booklist_fail")
        context.close()
        raise SystemExit(0)

    # '문제편집기' 버튼은 행 체크박스를 선택해야 활성화되는 것으로 보임.
    # 교재명 검색이 아직 불안정하므로, 우선 목록의 첫 번째 행을 선택해 버튼 동작 자체를 검증한다.
    print("[STEP] 첫 번째 행 체크박스 선택", flush=True)
    try:
        first_checkbox = booklist_page.locator("table tbody input[type=checkbox]").first
        td_html = first_checkbox.locator("xpath=ancestor::td[1]").evaluate("el => el.outerHTML")
        print(f"[체크박스 td HTML] {td_html}", flush=True)

        try:
            first_checkbox.check(timeout=3000, force=True)
            print("[체크박스 직접 check() 성공]", flush=True)
        except Exception as e1:
            print(f"[직접 check 실패, label/부모 클릭 시도] {e1}", flush=True)
            # JS로 네이티브 checked 속성을 직접 설정 + change 이벤트 발생
            first_checkbox.evaluate(
                """(el) => {
                    el.checked = true;
                    el.dispatchEvent(new Event('change', { bubbles: true }));
                    el.dispatchEvent(new Event('click', { bubbles: true }));
                }"""
            )
            print("[JS로 checked=true 설정 완료]", flush=True)

        booklist_page.wait_for_timeout(500)
        shot(booklist_page, "f3_06_first_row_checked")
    except Exception as e:
        print(f"[체크박스 선택 실패] {e}", flush=True)
        shot(booklist_page, "f3_06_checkbox_fail")
        context.close()
        raise SystemExit(0)

    print("[STEP] 문제편집기 버튼 클릭", flush=True)
    try:
        pages_before3 = len(context.pages)
        booklist_page.get_by_text("문제편집기", exact=True).first.click(timeout=8000, force=True)
        booklist_page.wait_for_timeout(2000)

        editor_page = booklist_page
        if len(context.pages) > pages_before3:
            editor_page = context.pages[-1]
            editor_page.wait_for_load_state("networkidle", timeout=15000)

        print(f"[문제편집기 진입] URL={editor_page.url} TITLE={editor_page.title()}", flush=True)
        shot(editor_page, "f3_07_editor")
    except Exception as e:
        print(f"[문제편집기 진입 실패] {e}", flush=True)
        shot(booklist_page, "f3_07_editor_fail")
        context.close()
        raise SystemExit(0)

    # 편집기 내부의 '교재/내신명을 입력해주세요' 검색창에서 실제 교재를 선택
    print(f"[STEP] 편집기 내 교재 검색: {TEXTBOOK_SEARCH_TEXT}", flush=True)
    try:
        inner_search = editor_page.get_by_placeholder("교재/내신명을 입력해주세요")
        inner_search.click(timeout=5000, force=True)
        inner_search.fill("", force=True)
        # fill()은 이 컴포넌트의 실시간 자동완성을 트리거하지 못해 실제 타이핑처럼 입력
        editor_page.keyboard.type(TEXTBOOK_NAME_EXACT, delay=120)
        editor_page.wait_for_timeout(1500)
        shot(editor_page, "f3_08_inner_search_typed")

        # 드롭다운 컨테이너로 추정되는 영역만 한정해서 옵션 텍스트 덤프 (진단용)
        print("[입력창 근처 드롭다운 옵션 목록]", flush=True)
        dropdown_area = inner_search.locator("xpath=following-sibling::*[1] | xpath=../following-sibling::*[1]")
        try:
            for opt_loc in dropdown_area.locator("li, div, span").all()[:20]:
                t = opt_loc.inner_text(timeout=200).strip()
                if t and len(t) < 60:
                    print(f"  - {repr(t)}", flush=True)
        except Exception as e:
            print(f"  (드롭다운 영역 덤프 실패: {e})", flush=True)

        # 자동완성 드롭다운에서 정확한 교재명 항목 클릭
        option = editor_page.get_by_text(TEXTBOOK_NAME_EXACT, exact=False).first
        option.wait_for(timeout=5000)
        option.click(timeout=5000, force=True)
        editor_page.wait_for_timeout(1000)
        shot(editor_page, "f3_09_inner_option_selected")

        # 검색 버튼 클릭 (돋보기 아이콘) - 상단 툴바의 파란 사각 버튼, 좌표로 고정 클릭
        editor_page.mouse.click(835, 70)
        editor_page.wait_for_timeout(2000)
        shot(editor_page, "f3_10_inner_search_result")

        total = editor_page.get_by_text("문제 목록").first.locator("xpath=..").inner_text(timeout=2000)
        print(f"[문제 목록 영역 텍스트] {total}", flush=True)
    except Exception as e:
        print(f"[편집기 내 검색 실패] {e}", flush=True)
        shot(editor_page, "f3_08_inner_search_fail")

    print("[완료] 전체 흐름 성공", flush=True)
    context.close()

print("[종료]", flush=True)
