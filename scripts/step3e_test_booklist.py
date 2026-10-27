# STEP 3e: 교재관리(booklist) 페이지 직접 접근 테스트 + 구조 확인
from pathlib import Path
from playwright.sync_api import sync_playwright

BASE_DIR = Path(__file__).parent.parent
USER_DATA_DIR = BASE_DIR / ".browser_profile"
TARGET_URL = "https://odapnote.t-ime.com/booklist"

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
    page.wait_for_timeout(2000)

    print(f"[현재 URL] {page.url}", flush=True)
    print(f"[현재 타이틀] {page.title()}", flush=True)

    screenshot_path = BASE_DIR / "data" / "step3e_booklist.png"
    page.screenshot(path=str(screenshot_path))
    print(f"[스크린샷 저장] {screenshot_path}", flush=True)

    # 검색창, 버튼 등 input/button 요소 텍스트 덤프
    print("\n[버튼 목록]", flush=True)
    for btn in page.locator("button").all():
        try:
            txt = btn.inner_text(timeout=500).strip()
            if txt:
                print(f"  - button: {repr(txt)}", flush=True)
        except Exception:
            pass

    print("\n[input placeholder 목록]", flush=True)
    for inp in page.locator("input").all():
        try:
            ph = inp.get_attribute("placeholder")
            if ph:
                print(f"  - input placeholder: {repr(ph)}", flush=True)
        except Exception:
            pass

    context.close()

print("[완료]", flush=True)
