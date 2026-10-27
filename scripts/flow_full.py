# 전체 흐름을 한 번의 실행에서 끊김 없이 처리 (세션 유지 목적)
# M.Connect 로그인 -> 그리드메뉴 -> 엠노트 -> 오답노트 -> 교재등록 -> 검색/선택 -> 문제편집기
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


def dump_texts(page, label, selector="a, button, div[role=button], li"):
    print(f"[{label} - 보이는 텍스트 요소 덤프]", flush=True)
    try:
        for loc in page.locator(selector).all()[:60]:
            try:
                txt = loc.inner_text(timeout=200).strip()
                if txt and len(txt) < 30:
                    print(f"  - {repr(txt)}", flush=True)
            except Exception:
                pass
    except Exception as e:
        print(f"  덤프 실패: {e}", flush=True)


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
        shot(page, "full_01_login_failed")
        context.close()
        raise SystemExit(0)

    print("[STEP] 그리드 메뉴 열기", flush=True)
    page.mouse.click(1524, 24)
    page.wait_for_timeout(800)
    shot(page, "full_02_grid")

    print("[STEP] 엠노트 클릭", flush=True)
    mnote_page = None
    try:
        with context.expect_page(timeout=8000) as info:
            page.get_by_text("엠노트", exact=True).first.click(timeout=5000)
        mnote_page = info.value
        mnote_page.wait_for_load_state("networkidle", timeout=20000)
    except Exception as e:
        print(f"[새 탭 감지 실패] {e}", flush=True)
        # 혹시 현재 탭에서 이동했는지 확인
        page.wait_for_timeout(2000)
        if not page.is_closed() and "mswitch" not in page.url.lower():
            mnote_page = page

    if mnote_page is None or mnote_page.is_closed():
        print("[중단] 엠노트 진입 실패", flush=True)
        if not page.is_closed():
            shot(page, "full_03_mnote_fail")
        context.close()
        raise SystemExit(0)

    print(f"[엠노트 진입 성공] URL={mnote_page.url} TITLE={mnote_page.title()}", flush=True)
    shot(mnote_page, "full_03_mnote_home")
    dump_texts(mnote_page, "엠노트 홈")

    print("[STEP] 오답노트 메뉴 클릭", flush=True)
    try:
        mnote_page.get_by_text("오답노트", exact=True).first.click(timeout=8000)
        mnote_page.wait_for_timeout(1000)
        shot(mnote_page, "full_04_odapnote_menu")
        dump_texts(mnote_page, "오답노트 드롭다운")
    except Exception as e:
        print(f"[오답노트 클릭 실패] {e}", flush=True)
        shot(mnote_page, "full_04_odapnote_fail")
        context.close()
        raise SystemExit(0)

    print("[STEP] 교재등록 메뉴 클릭", flush=True)
    booklist_page = mnote_page
    try:
        pages_before = len(context.pages)
        mnote_page.get_by_text("교재등록", exact=True).first.click(timeout=8000)
        mnote_page.wait_for_timeout(1500)
        if len(context.pages) > pages_before:
            booklist_page = context.pages[-1]
            booklist_page.wait_for_load_state("networkidle", timeout=15000)
        shot(booklist_page, "full_05_booklist")
        print(f"[교재등록 진입] URL={booklist_page.url}", flush=True)
    except Exception as e:
        print(f"[교재등록 클릭 실패] {e}", flush=True)
        shot(mnote_page, "full_05_booklist_fail")
        context.close()
        raise SystemExit(0)

    print(f"[STEP] 교재명 검색: {TEXTBOOK_SEARCH_TEXT}", flush=True)
    try:
        search_input = booklist_page.get_by_placeholder("검색을 해주세요")
        search_input.click(timeout=5000)
        search_input.fill(TEXTBOOK_SEARCH_TEXT)
        search_input.press("Enter")
        booklist_page.wait_for_timeout(1500)
        shot(booklist_page, "full_06_search_result")
    except Exception as e:
        print(f"[검색 실패] {e}", flush=True)
        shot(booklist_page, "full_06_search_fail")
        context.close()
        raise SystemExit(0)

    print("[STEP] 결과 행 체크박스 선택 및 문제편집기 클릭", flush=True)
    try:
        row = booklist_page.get_by_text(TEXTBOOK_NAME_EXACT, exact=False).first
        row.wait_for(timeout=8000)
        # 같은 행(tr) 안의 체크박스 클릭
        tr = row.locator("xpath=ancestor::tr[1]")
        checkbox = tr.locator("input[type=checkbox]").first
        checkbox.click(timeout=5000)
        booklist_page.wait_for_timeout(500)
        shot(booklist_page, "full_07_row_checked")

        pages_before = len(context.pages)
        booklist_page.get_by_text("문제편집기", exact=True).first.click(timeout=8000)
        booklist_page.wait_for_timeout(2000)

        editor_page = booklist_page
        if len(context.pages) > pages_before:
            editor_page = context.pages[-1]
            editor_page.wait_for_load_state("networkidle", timeout=15000)

        print(f"[문제편집기 진입] URL={editor_page.url} TITLE={editor_page.title()}", flush=True)
        shot(editor_page, "full_08_editor")
    except Exception as e:
        print(f"[문제편집기 진입 실패] {e}", flush=True)
        shot(booklist_page, "full_08_editor_fail")
        context.close()
        raise SystemExit(0)

    print("[완료] 전체 흐름 성공", flush=True)
    context.close()

print("[종료]", flush=True)
