# 흐름 5단계: 그리드 메뉴를 열고 '엠노트' 링크의 href를 직접 확인
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

    print("[모든 a 태그 href 덤프]", flush=True)
    for a in page.locator("a").all():
        try:
            href = a.get_attribute("href")
            txt = a.inner_text(timeout=200).strip()
            if href and href not in ("#", "javascript:void(0)"):
                print(f"  text={repr(txt)} href={href}", flush=True)
        except Exception:
            pass

    print("\n[모든 클릭 가능 요소(div/li 등) onclick 속성 덤프]", flush=True)
    for el in page.locator("[onclick]").all():
        try:
            txt = el.inner_text(timeout=200).strip()
            onclick = el.get_attribute("onclick")
            if txt:
                print(f"  text={repr(txt)} onclick={onclick}", flush=True)
        except Exception:
            pass

    context.close()
print("[완료]", flush=True)
