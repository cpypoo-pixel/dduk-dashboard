# STEP 3d: 저장된 로그인 세션으로 문제편집기 딥링크가 바로 열리는지 테스트
from pathlib import Path
from playwright.sync_api import sync_playwright

BASE_DIR = Path(__file__).parent.parent
USER_DATA_DIR = BASE_DIR / ".browser_profile"
TARGET_URL = "https://adm.mswitch.co.kr/api/in/mnote-bank/book-item-edit?book_type=02&group_code=SNB0000200&center_seq=664"

with sync_playwright() as p:
    context = p.chromium.launch_persistent_context(
        str(USER_DATA_DIR),
        headless=False,
        viewport={"width": 1600, "height": 1000},
    )
    for p_old in list(context.pages)[1:]:
        try:
            p_old.close()
        except Exception:
            pass
    page = context.pages[0] if context.pages else context.new_page()

    print(f"[이동 시도] {TARGET_URL}", flush=True)
    page.goto(TARGET_URL, timeout=20000, wait_until="networkidle")
    page.wait_for_timeout(3000)

    print(f"[현재 URL] {page.url}", flush=True)
    print(f"[현재 타이틀] {page.title()}", flush=True)

    screenshot_path = BASE_DIR / "data" / "step3d_deeplink.png"
    page.screenshot(path=str(screenshot_path))
    print(f"[스크린샷 저장] {screenshot_path}", flush=True)

    context.close()

print("[완료]", flush=True)
