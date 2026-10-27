# 전체 흐름 v2: href 기반 이동 우선 시도 + 클릭 폴백, 전부 한 세션 안에서 처리
from pathlib import Path
from playwright.sync_api import sync_playwright

BASE_DIR = Path(__file__).parent.parent
DATA_DIR = BASE_DIR / "data"
USER_DATA_DIR = BASE_DIR / ".browser_profile"
LOGIN_WAIT_SECONDS = 120
TEXTBOOK_SEARCH_TEXT = "셀B"
TEXTBOOK_NAME_EXACT = "고1 2학기 2022개정 수학 셀B 공통수학2"


def shot(page, name):
    path = DATA_DIR / f"{name}.png"
    try:
        page.screenshot(path=str(path))
        print(f"[스크린샷] {path}", flush=True)
    except Exception as e:
        print(f"[스크린샷 실패:{name}] {e}", flush=True)


def find_href(page, text):
    try:
        loc = page.get_by_text(text, exact=True).first
        href = loc.locator("xpath=ancestor-or-self::a[1]").get_attribute("href", timeout=2000)
        return href
    except Exception:
        return None


def smart_navigate(page, context, text, label):
    """text가 href를 가진 링크면 새 탭으로 직접 열고, 아니면 클릭으로 폴백."""
    href = find_href(page, text)
    print(f"[{label}] href 탐색 결과: {href}", flush=True)

    if href and href.startswith("http"):
        new_page = context.new_page()
        new_page.goto(href, timeout=20000, wait_until="networkidle")
        print(f"[{label}] href로 직접 이동 성공: {new_page.url}", flush=True)
        return new_page

    # 클릭 폴백
    pages_before = len(context.pages)
    try:
        with context.expect_page(timeout=6000) as info:
            page.get_by_text(text, exact=True).first.click(timeout=5000)
        new_page = info.value
        new_page.wait_for_load_state("networkidle", timeout=15000)
        print(f"[{label}] 클릭으로 새 탭 열림: {new_page.url}", flush=True)
        return new_page
    except Exception as e:
        print(f"[{label}] 클릭 새탭 감지 실패: {e}", flush=True)
        if not page.is_closed():
            page.wait_for_timeout(1500)
            if len(context.pages) > pages_before:
                np = context.pages[-1]
                print(f"[{label}] 폴링으로 새 탭 발견: {np.url}", flush=True)
                return np
            print(f"[{label}] 같은 탭 유지, URL={page.url}", flush=True)
            return page
        print(f"[{label}] 원본 탭도 닫힘", flush=True)
        return None


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
    print(f"[안내] 로그인 확인 중... URL={page.url}", flush=True)
    if "/login" in page.url:
        print(f"[대기] {LOGIN_WAIT_SECONDS}초 동안 로그인해 주세요.", flush=True)
        page.wait_for_timeout(LOGIN_WAIT_SECONDS * 1000)
        page.goto("https://adm.mswitch.co.kr/", timeout=20000, wait_until="networkidle")

    page.wait_for_timeout(1000)
    print(f"[현재 URL] {page.url}", flush=True)
    if "/login" in page.url:
        print("[중단] 로그인되지 않았습니다.", flush=True)
        shot(page, "f2_01_login_failed")
        context.close()
        raise SystemExit(0)

    print("[STEP] 그리드 메뉴 열기", flush=True)
    page.mouse.click(1524, 24)
    page.wait_for_timeout(800)
    shot(page, "f2_02_grid")

    mnote_page = smart_navigate(page, context, "엠노트", "엠노트 진입")
    if mnote_page is None:
        context.close()
        raise SystemExit(0)
    shot(mnote_page, "f2_03_mnote_home")

    print("[STEP] 오답노트 메뉴 클릭 (같은 페이지 내 드롭다운일 가능성)", flush=True)
    try:
        mnote_page.get_by_text("오답노트", exact=True).first.click(timeout=8000)
        mnote_page.wait_for_timeout(1000)
        shot(mnote_page, "f2_04_odapnote_menu")
    except Exception as e:
        print(f"[오답노트 클릭 실패] {e}", flush=True)
        shot(mnote_page, "f2_04_odapnote_fail")
        context.close()
        raise SystemExit(0)

    booklist_page = smart_navigate(mnote_page, context, "교재등록", "교재등록 진입")
    if booklist_page is None:
        context.close()
        raise SystemExit(0)
    shot(booklist_page, "f2_05_booklist")
    print(f"[교재등록 URL] {booklist_page.url}", flush=True)

    print(f"[STEP] 교재명 검색: {TEXTBOOK_SEARCH_TEXT}", flush=True)
    try:
        search_input = booklist_page.get_by_placeholder("검색을 해주세요")
        search_input.click(timeout=5000)
        search_input.fill(TEXTBOOK_SEARCH_TEXT)
        search_input.press("Enter")
        booklist_page.wait_for_timeout(1500)
        shot(booklist_page, "f2_06_search_result")
    except Exception as e:
        print(f"[검색 실패] {e}", flush=True)
        shot(booklist_page, "f2_06_search_fail")
        context.close()
        raise SystemExit(0)

    print("[STEP] 결과 행 체크박스 선택 및 문제편집기 클릭", flush=True)
    try:
        row = booklist_page.get_by_text(TEXTBOOK_NAME_EXACT, exact=False).first
        row.wait_for(timeout=8000)
        tr = row.locator("xpath=ancestor::tr[1]")
        checkbox = tr.locator("input[type=checkbox]").first
        checkbox.click(timeout=5000)
        booklist_page.wait_for_timeout(500)
        shot(booklist_page, "f2_07_row_checked")

        editor_page = smart_navigate(booklist_page, context, "문제편집기", "문제편집기 진입")
        if editor_page is None:
            context.close()
            raise SystemExit(0)

        print(f"[문제편집기 진입] URL={editor_page.url} TITLE={editor_page.title()}", flush=True)
        shot(editor_page, "f2_08_editor")
    except Exception as e:
        print(f"[문제편집기 진입 실패] {e}", flush=True)
        shot(booklist_page, "f2_08_editor_fail")
        context.close()
        raise SystemExit(0)

    print("[완료] 전체 흐름 성공", flush=True)
    context.close()

print("[종료]", flush=True)
