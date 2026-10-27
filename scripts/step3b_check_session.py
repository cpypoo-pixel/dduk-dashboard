# STEP 3b: 로그인 세션이 유지되는지 빠르게 확인
from pathlib import Path
from playwright.sync_api import sync_playwright

BASE_DIR = Path(__file__).parent.parent
USER_DATA_DIR = BASE_DIR / ".browser_profile"
ADMIN_URL = "https://adm.mswitch.co.kr/api/in/mnote-bank/book-item-edit?group_code=SNB0000200&center_seq=664"

with sync_playwright() as p:
    context = p.chromium.launch_persistent_context(
        str(USER_DATA_DIR),
        headless=False,
        viewport={"width": 1600, "height": 1000},
    )
    page = context.pages[0] if context.pages else context.new_page()
    page.goto(ADMIN_URL)
    page.wait_for_timeout(5000)

    print(f"[현재 URL] {page.url}")
    print(f"[현재 타이틀] {page.title()}")

    screenshot_path = BASE_DIR / "data" / "step3b_session_check.png"
    page.screenshot(path=str(screenshot_path), full_page=False)
    print(f"[스크린샷 저장] {screenshot_path}")

    context.close()

print("[완료]")
