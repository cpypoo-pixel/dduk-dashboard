# 흐름 1단계: M.Connect 로그인 상태 확인
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
    print(f"[현재 타이틀] {page.title()}", flush=True)
    logged_in = "/login" not in page.url
    print(f"[로그인 상태] {'로그인됨' if logged_in else '로그인 필요'}", flush=True)

    page.screenshot(path=str(BASE_DIR / "data" / "flow_01.png"))

    context.close()
print("[완료]", flush=True)
