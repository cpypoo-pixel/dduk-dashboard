# 흐름 4단계: 그리드 메뉴를 열고 '엠노트' 텍스트 요소의 정확한 좌표를 찾는다
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
    page.wait_for_timeout(1500)
    print(f"[현재 URL] {page.url}", flush=True)
    if "/login" in page.url:
        print("[중단] 로그인 필요", flush=True)
        context.close()
        raise SystemExit(0)

    page.mouse.click(1524, 24)
    page.wait_for_timeout(1000)

    locs = page.get_by_text("엠노트").all()
    print(f"[찾은 요소 수] {len(locs)}", flush=True)
    for i, loc in enumerate(locs):
        try:
            box = loc.bounding_box()
            txt = loc.inner_text(timeout=500)
            print(f"  [{i}] text={repr(txt)} box={box}", flush=True)
        except Exception as e:
            print(f"  [{i}] 오류: {e}", flush=True)

    page.screenshot(path=str(BASE_DIR / "data" / "flow_04_menu_open.png"))

    context.close()
print("[완료]", flush=True)
