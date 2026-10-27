# STEP 3c: 로그인 세션이 저장됐는지 확인 (루트 도메인 접속 후 상태 캡처)
from pathlib import Path
from playwright.sync_api import sync_playwright

BASE_DIR = Path(__file__).parent.parent
USER_DATA_DIR = BASE_DIR / ".browser_profile"

with sync_playwright() as p:
    context = p.chromium.launch_persistent_context(
        str(USER_DATA_DIR),
        headless=False,
        viewport={"width": 1600, "height": 1000},
    )
    page = context.pages[0] if context.pages else context.new_page()
    page.goto("https://adm.mswitch.co.kr/")
    page.wait_for_timeout(5000)

    print(f"[현재 URL] {page.url}")
    print(f"[현재 타이틀] {page.title()}")

    screenshot_path = BASE_DIR / "data" / "step3c_login_check.png"
    page.screenshot(path=str(screenshot_path))
    print(f"[스크린샷 저장] {screenshot_path}")

    context.close()

print("[완료]")
