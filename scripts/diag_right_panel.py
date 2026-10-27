# 진단 전용: 문제편집기 오른쪽 상세 패널의 실제 HTML 구조를 덤프
from pathlib import Path
from playwright.sync_api import sync_playwright

BASE_DIR = Path(__file__).parent.parent
USER_DATA_DIR = BASE_DIR / ".browser_profile"
LOGIN_WAIT_SECONDS = 180
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
        print("[중단] 로그인 실패", flush=True)
        context.close()
        raise SystemExit(0)
    print(f"[로그인 확인] {page.url}", flush=True)

    pages_before = len(context.pages)
    mnote_page = None
    for attempt in range(1, 9):
        page.mouse.click(1524, 24)
        page.wait_for_timeout(700)
        page.evaluate(JS_CLICK_BY_TEXT, "엠노트")
        page.wait_for_timeout(2000)
        if len(context.pages) > pages_before:
            mnote_page = context.pages[-1]
            break
    if mnote_page is None:
        print("[중단] 엠노트 진입 실패", flush=True)
        context.close()
        raise SystemExit(0)
    mnote_page.wait_for_load_state("networkidle", timeout=15000)
    print(f"[엠노트 진입] {mnote_page.url}", flush=True)

    booklist_page = mnote_page
    for attempt in range(1, 6):
        try:
            target = mnote_page.get_by_text("교재등록", exact=True).first
            if not target.is_visible():
                mnote_page.get_by_text("오답노트", exact=True).first.click(timeout=5000, force=True)
                mnote_page.wait_for_timeout(600)
            pages_before2 = len(context.pages)
            target.click(timeout=5000, force=True)
            mnote_page.wait_for_timeout(1500)
            if len(context.pages) > pages_before2:
                booklist_page = context.pages[-1]
                booklist_page.wait_for_load_state("networkidle", timeout=15000)
            if "/booklist" in booklist_page.url:
                break
        except Exception:
            pass
    print(f"[교재등록] {booklist_page.url}", flush=True)

    first_checkbox = booklist_page.locator("table tbody input[type=checkbox]").first
    try:
        first_checkbox.check(timeout=3000, force=True)
    except Exception:
        first_checkbox.evaluate(
            """(el) => { el.checked = true; el.dispatchEvent(new Event('change', {bubbles:true})); }"""
        )
    booklist_page.wait_for_timeout(500)

    pages_before3 = len(context.pages)
    booklist_page.get_by_text("문제편집기", exact=True).first.click(timeout=8000, force=True)
    booklist_page.wait_for_timeout(2000)
    editor_page = booklist_page
    if len(context.pages) > pages_before3:
        editor_page = context.pages[-1]
        editor_page.wait_for_load_state("networkidle", timeout=15000)
    print(f"[문제편집기] {editor_page.url}", flush=True)

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
    print("[교재 로드 완료]", flush=True)

    # ---- 진단: 오른쪽 상세 패널 HTML 덤프 ----
    print("\n[진단] '문제코드' 텍스트를 포함하는 모든 매칭 요소와 위치", flush=True)
    candidates = editor_page.get_by_text("문제코드", exact=True).all()
    print(f"매칭 개수: {len(candidates)}", flush=True)
    for i, cand in enumerate(candidates):
        try:
            visible = cand.is_visible()
            box = cand.bounding_box()
            print(f"  [{i}] visible={visible} box={box}", flush=True)
        except Exception as e:
            print(f"  [{i}] 오류: {e}", flush=True)

    # 화면 우측(x>1330)에 있는 것을 진짜 패널로 간주하고 그 조상 컨테이너 HTML 덤프
    print("\n[진단] 우측 패널(x>1330) 후보의 조상 HTML (최대 2000자)", flush=True)
    for i, cand in enumerate(candidates):
        try:
            box = cand.bounding_box()
            if box and box["x"] > 1330:
                container = cand.locator("xpath=ancestor::*[position()<=4]").last
                html = container.evaluate("el => el.outerHTML")
                print(f"  [{i}] HTML:\n{html[:2500]}", flush=True)
        except Exception as e:
            print(f"  [{i}] 오류: {e}", flush=True)

    editor_page.screenshot(path=str(BASE_DIR / "data" / "diag_panel.png"))
    context.close()
print("[완료]", flush=True)
