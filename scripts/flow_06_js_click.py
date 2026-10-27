# 흐름 6단계: JS로 '엠노트' 요소를 찾아 구조를 덤프하고, 네이티브 click()을 직접 실행
from pathlib import Path
from playwright.sync_api import sync_playwright

BASE_DIR = Path(__file__).parent.parent
USER_DATA_DIR = BASE_DIR / ".browser_profile"

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
    page.wait_for_timeout(1000)
    print(f"[현재 URL] {page.url}", flush=True)
    if "/login" in page.url:
        print("[중단] 로그인 필요", flush=True)
        context.close()
        raise SystemExit(0)

    page.mouse.click(1524, 24)
    page.wait_for_timeout(800)

    # '엠노트' 텍스트를 포함하는 요소와 그 조상 체인의 태그/클래스/onclick을 덤프
    info = page.evaluate("""
    () => {
        const walker = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT);
        let node;
        let results = [];
        while (node = walker.nextNode()) {
            if (node.textContent.trim() === '엠노트') {
                let el = node.parentElement;
                let chain = [];
                let cur = el;
                for (let i = 0; i < 5 && cur; i++) {
                    chain.push({
                        tag: cur.tagName,
                        cls: cur.className,
                        id: cur.id,
                        onclick: cur.getAttribute('onclick'),
                        role: cur.getAttribute('role'),
                        href: cur.getAttribute('href'),
                    });
                    cur = cur.parentElement;
                }
                results.push(chain);
            }
        }
        return results;
    }
    """)
    print("[엠노트 텍스트 조상 체인]", flush=True)
    for chain in info:
        for item in chain:
            print(f"  {item}", flush=True)
        print("  ---", flush=True)

    pages_before = len(context.pages)
    js_click = """
    () => {
        const walker = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT);
        let node;
        while (node = walker.nextNode()) {
            if (node.textContent.trim() === '엠노트') {
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

    # 사용자 제보: 한 번에 안 되고 여러 번 시도해야 할 수 있음 -> 최대 5회 재시도
    new_tab_found = False
    for attempt in range(1, 6):
        print(f"[시도 {attempt}/5] 그리드 메뉴 열기 + 엠노트 클릭", flush=True)
        if page.is_closed():
            print("  원본 탭이 닫혀 중단", flush=True)
            break
        try:
            page.mouse.click(1524, 24)
            page.wait_for_timeout(500)
            clicked = page.evaluate(js_click)
            print(f"  [JS 클릭 결과] {clicked}", flush=True)
        except Exception as e:
            print(f"  [클릭 중 예외] {e}", flush=True)

        page.wait_for_timeout(2000)
        if len(context.pages) > pages_before:
            new_tab_found = True
            print(f"  [새 탭 발견] 탭 수: {len(context.pages)}", flush=True)
            break
        else:
            print("  [새 탭 없음] 재시도합니다...", flush=True)

    print(f"[최종 탭 수] {len(context.pages)} (이전 {pages_before})", flush=True)
    for i, p_tab in enumerate(context.pages):
        if not p_tab.is_closed():
            print(f"  탭{i}: {p_tab.url}", flush=True)

    if new_tab_found:
        new_page = context.pages[-1]
        try:
            new_page.wait_for_load_state("networkidle", timeout=15000)
        except Exception as e:
            print(f"[새 탭 로드 대기 예외] {e}", flush=True)
        print(f"[새 탭 URL] {new_page.url}", flush=True)
        print(f"[새 탭 타이틀] {new_page.title()}", flush=True)
        new_page.screenshot(path=str(BASE_DIR / "data" / "flow_06_newtab.png"))
        print("[스크린샷] flow_06_newtab.png", flush=True)
    elif not page.is_closed():
        page.screenshot(path=str(BASE_DIR / "data" / "flow_06_after_jsclick.png"))
        print("[스크린샷] flow_06_after_jsclick.png", flush=True)

    context.close()
print("[완료]", flush=True)
