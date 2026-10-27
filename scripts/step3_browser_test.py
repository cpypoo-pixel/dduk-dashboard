# STEP 3: Playwright 브라우저 자동화 환경 테스트
# - 브라우저를 열어 관리자 페이지로 이동만 한다.
# - 로그인은 사용자가 직접 수행한다 (아이디/비밀번호를 코드에 넣지 않음).
# - 로그인 세션 쿠키는 user_data_dir에 브라우저 자체적으로 저장되어,
#   다음 실행부터는 재로그인 없이 이어서 사용할 수 있다 (코드로 값을 읽지 않음).
import sys
import time
from pathlib import Path
from playwright.sync_api import sync_playwright, TimeoutError as PwTimeoutError

BASE_DIR = Path(__file__).parent.parent
USER_DATA_DIR = BASE_DIR / ".browser_profile"  # 로그인 세션 저장용 (git에 올리지 말 것)
ADMIN_URL = "https://adm.mswitch.co.kr/"  # 이전에 로그인 성공이 확인된 주소
WAIT_SECONDS = 560  # 이 시간 동안 사용자가 직접 로그인 및 화면 이동

USER_DATA_DIR.mkdir(parents=True, exist_ok=True)

print("[1/5] 브라우저 실행 중...", flush=True)
with sync_playwright() as p:
    context = p.chromium.launch_persistent_context(
        str(USER_DATA_DIR),
        headless=False,
        viewport={"width": 1600, "height": 1000},
    )
    print(f"[2/5] 브라우저 실행됨. 세션 복원된 탭 수: {len(context.pages)}", flush=True)

    # 이전 세션에서 복원된 탭이 많으면 헷갈리므로, 전부 닫고 새 탭 하나만 사용
    for p_old in list(context.pages):
        try:
            p_old.close()
        except Exception:
            pass
    page = context.new_page()
    print("[3/5] 새 탭 생성 완료. 페이지 이동 시도...", flush=True)

    try:
        page.goto(ADMIN_URL, timeout=20000, wait_until="domcontentloaded")
        print(f"[4/5] 이동 성공: {page.url}", flush=True)
    except PwTimeoutError:
        print(f"[4/5] 이동 실패(20초 타임아웃): {ADMIN_URL}", flush=True)
        print("[안내] 네트워크 문제일 수 있습니다. 브라우저 창에서 직접 주소창에 입력해 이동해 주세요.", flush=True)

    print(f"[5/5] {WAIT_SECONDS}초 동안 대기합니다. 브라우저 창에서 직접 이동해 주세요.", flush=True)
    time.sleep(WAIT_SECONDS)

    # 열려 있는 모든 탭을 캡처 (닫힌 탭은 건너뜀)
    print(f"[열려 있는 탭 수] {len(context.pages)}", flush=True)
    for i, p_tab in enumerate(context.pages):
        if p_tab.is_closed():
            print(f"--- 탭 {i}: 닫힘, 건너뜀 ---", flush=True)
            continue
        print(f"--- 탭 {i} ---", flush=True)
        try:
            print(f"[URL] {p_tab.url}", flush=True)
            print(f"[타이틀] {p_tab.title()}", flush=True)
            screenshot_path = BASE_DIR / "data" / f"step3_tab{i}.png"
            p_tab.screenshot(path=str(screenshot_path))
            print(f"[스크린샷 저장] {screenshot_path}", flush=True)
        except Exception as e:
            print(f"[탭 {i} 처리 실패] {e}", flush=True)

    context.close()

print("[완료] 브라우저를 닫았습니다. 로그인 세션은 .browser_profile 폴더에 유지됩니다.", flush=True)
