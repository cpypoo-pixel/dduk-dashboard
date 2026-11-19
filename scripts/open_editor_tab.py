# -*- coding: utf-8 -*-
"""떠 있는 CDP Chrome(9333)에 붙어서 홈 -> 엠노트 -> 교재등록 -> 첫 행 선택 -> 문제편집기(book-item-edit 탭)까지 이동한다.
flow_full3.py의 경로를 그대로 따르되 새 브라우저를 띄우지 않는다."""
from playwright.sync_api import sync_playwright

JS_CLICK_BY_TEXT = """
(targetText) => {
    const walker = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT);
    let node;
    while (node = walker.nextNode()) {
        if (node.textContent.trim() === targetText) {
            let cur = node.parentElement;
            for (let i = 0; i < 6 && cur; i++) {
                if (cur.tagName === 'A' || cur.tagName === 'BUTTON' || cur.onclick || cur.getAttribute('role') === 'button') {
                    cur.click();
                    return 'clicked:' + cur.tagName;
                }
                cur = cur.parentElement;
            }
            node.parentElement.click();
            return 'clicked-fallback-leaf';
        }
    }
    return 'not-found';
}
"""


def has_editor(ctx):
    return any("book-item-edit" in pg.url for pg in ctx.pages)


with sync_playwright() as p:
    browser = p.chromium.connect_over_cdp("http://localhost:9333")
    ctx = browser.contexts[0]
    home = None
    for pg in ctx.pages:
        if pg.url.rstrip("/").endswith("adm.mswitch.co.kr/home"):
            home = pg
    if home is None:
        home = ctx.pages[0]
        home.goto("https://adm.mswitch.co.kr/home", timeout=20000, wait_until="networkidle")
    home.wait_for_load_state("networkidle", timeout=30000)
    home.wait_for_selector("body", timeout=10000)
    print("[홈]", home.url, flush=True)
    if "/login" in home.url:
        print("[중단] 로그인이 필요합니다.", flush=True)
        raise SystemExit(0)

    before = len(ctx.pages)
    mnote = None
    for attempt in range(1, 9):
        print(f"[엠노트 진입 시도 {attempt}/8]", flush=True)
        try:
            home.keyboard.press("Escape")
            g = home.get_by_text("전체서비스", exact=True).first
            if g.count() > 0:
                g.click(timeout=2000, force=True)
        except Exception as e:
            print("  전체서비스 클릭 실패:", e, flush=True)
        home.wait_for_timeout(800)
        try:
            print("  ", home.evaluate(JS_CLICK_BY_TEXT, "엠노트"), flush=True)
        except Exception as e:
            print("  엠노트 클릭 실패:", str(e).splitlines()[0], flush=True)
        home.wait_for_timeout(2500)
        if len(ctx.pages) > before:
            mnote = ctx.pages[-1]
            break
    if mnote is None:
        print("[중단] 엠노트 진입 실패", flush=True)
        raise SystemExit(0)
    mnote.wait_for_load_state("networkidle", timeout=15000)
    print("[엠노트]", mnote.url, flush=True)

    mnote.get_by_text("오답노트", exact=True).first.click(timeout=8000)
    mnote.wait_for_timeout(800)
    before2 = len(ctx.pages)
    mnote.get_by_text("교재등록", exact=True).first.click(timeout=8000)
    mnote.wait_for_timeout(1500)
    booklist = ctx.pages[-1] if len(ctx.pages) > before2 else mnote
    booklist.wait_for_load_state("networkidle", timeout=15000)
    print("[교재등록]", booklist.url, flush=True)

    cb = booklist.locator("table tbody input[type=checkbox]").first
    try:
        cb.check(timeout=3000, force=True)
    except Exception:
        cb.evaluate("""el => { el.checked = true; el.dispatchEvent(new Event('change', {bubbles:true})); el.dispatchEvent(new Event('click', {bubbles:true})); }""")
    booklist.wait_for_timeout(500)

    before3 = len(ctx.pages)
    booklist.get_by_text("문제편집기", exact=True).first.click(timeout=8000, force=True)
    booklist.wait_for_timeout(2500)
    editor = ctx.pages[-1] if len(ctx.pages) > before3 else booklist
    editor.wait_for_load_state("networkidle", timeout=15000)
    print("[문제편집기]", editor.url, flush=True)
    print("[결과] book-item-edit 탭 있음:", has_editor(ctx), flush=True)
