# 흐름 2단계: 로그인 대기 -> 그리드 메뉴 클릭 -> 엠노트 진입
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
        page.screenshot(path=str(BASE_DIR / "data" / "flow_02_not_logged_in.png"))
        context.close()
        raise SystemExit(0)

    print("[로그인 확인됨] 그리드 메뉴 아이콘을 찾는 중...", flush=True)
    # 우측 상단 그리드(점 9개) 아이콘 클릭 - 접근성 트리 기반으로 탐색
    grid_btn = page.locator("button, a, div[role=button]").filter(has=page.locator("svg")).last
    page.wait_for_timeout(500)

    # 좌표 기반 백업: 이전 스크린샷 기준 약 (1524, 24) 지점에 그리드 아이콘 존재
    page.mouse.click(1524, 24)
    page.wait_for_timeout(1000)
    page.screenshot(path=str(BASE_DIR / "data" / "flow_02_grid_clicked.png"))
    print("[스크린샷] flow_02_grid_clicked.png 저장", flush=True)

    # 엠노트 텍스트 클릭 시도 (새 탭으로 열릴 수 있음)
    try:
        with context.expect_page(timeout=5000) as new_page_info:
            page.get_by_text("엠노트", exact=True).first.click(timeout=5000)
        new_page = new_page_info.value
        new_page.wait_for_load_state("networkidle", timeout=15000)
        print(f"[새 탭 열림] URL: {new_page.url}", flush=True)
        print(f"[새 탭 타이틀] {new_page.title()}", flush=True)
        new_page.screenshot(path=str(BASE_DIR / "data" / "flow_02_mnote_newtab.png"))
        print("[스크린샷] flow_02_mnote_newtab.png 저장", flush=True)
    except Exception as e:
        print(f"[새 탭 감지 실패, 같은 탭에서 확인] {e}", flush=True)
        page.wait_for_timeout(2000)
        print(f"[현재 URL] {page.url}", flush=True)
        page.screenshot(path=str(BASE_DIR / "data" / "flow_02_mnote_sametab.png"))
        print("[스크린샷] flow_02_mnote_sametab.png 저장", flush=True)

    context.close()
print("[완료]", flush=True)
