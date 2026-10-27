# 흐름 3단계: 로그인 대기 -> 그리드 클릭 -> 엠노트 아이콘 좌표 클릭 -> 새 탭 폴링 감지
from pathlib import Path
from playwright.sync_api import sync_playwright

BASE_DIR = Path(__file__).parent.parent
USER_DATA_DIR = BASE_DIR / ".browser_profile"
LOGIN_WAIT_SECONDS = 90

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
    print(f"[안내] {LOGIN_WAIT_SECONDS}초 동안 대기합니다. 로그인이 필요하면 지금 해주세요.", flush=True)
    page.wait_for_timeout(LOGIN_WAIT_SECONDS * 1000)

    page.goto("https://adm.mswitch.co.kr/", timeout=20000, wait_until="networkidle")
    page.wait_for_timeout(1500)
    print(f"[현재 URL] {page.url}", flush=True)
    if "/login" in page.url:
        print("[중단] 아직 로그인되지 않았습니다.", flush=True)
        page.screenshot(path=str(BASE_DIR / "data" / "flow_03_not_logged_in.png"))
        context.close()
        raise SystemExit(0)

    print("[로그인 확인됨] 그리드 메뉴 클릭", flush=True)
    page.mouse.click(1524, 24)
    page.wait_for_timeout(1000)

    pages_before = len(context.pages)
    print(f"[엠노트 아이콘 좌표 클릭] (현재 탭 수: {pages_before})", flush=True)
    page.mouse.click(1502, 215)

    # 새 탭이 뜨는지 최대 10초 폴링
    new_page = None
    for _ in range(20):
        page.wait_for_timeout(500)
        if len(context.pages) > pages_before:
            new_page = context.pages[-1]
            break

    if new_page:
        print(f"[새 탭 감지됨] 탭 수: {len(context.pages)}", flush=True)
        try:
            new_page.wait_for_load_state("networkidle", timeout=15000)
        except Exception as e:
            print(f"[새 탭 로드 대기 중 예외] {e}", flush=True)
        print(f"[새 탭 URL] {new_page.url}", flush=True)
        print(f"[새 탭 타이틀] {new_page.title()}", flush=True)
        new_page.screenshot(path=str(BASE_DIR / "data" / "flow_03_mnote.png"))
        print("[스크린샷] flow_03_mnote.png 저장", flush=True)
    else:
        print("[새 탭 없음] 같은 탭에서 상태 확인", flush=True)
        if not page.is_closed():
            print(f"[현재 URL] {page.url}", flush=True)
            page.screenshot(path=str(BASE_DIR / "data" / "flow_03_sametab.png"))
            print("[스크린샷] flow_03_sametab.png 저장", flush=True)
        else:
            print("[원래 탭도 닫힘]", flush=True)

    context.close()
print("[완료]", flush=True)
