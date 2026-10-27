# -*- coding: utf-8 -*-
"""현재 선택된 교재(중1 1학기 2022개정 수학 최상위수학 라이트)의 엑셀 목록을
'엑셀다운로드' 버튼(#btn_excel_export) 클릭으로 다운로드한다.
조회(다운로드)만 수행하며 어떠한 데이터도 수정/삭제하지 않는다."""
import sys
from pathlib import Path
from playwright.sync_api import sync_playwright

sys.stdout.reconfigure(encoding="utf-8")

CDP_URL = "http://localhost:9333"
OUT_DIR = Path(r"D:\ddddashboard\data")
OUT_DIR.mkdir(exist_ok=True)

with sync_playwright() as p:
    browser = p.chromium.connect_over_cdp(CDP_URL)
    context = browser.contexts[0]
    target = None
    for pg in context.pages:
        if "book-item-edit" in pg.url:
            target = pg
    if target is None:
        print("[오류] book-item-edit 탭을 찾지 못했습니다.")
        raise SystemExit(1)

    target.bring_to_front()
    print(f"[대상 탭] {target.url}")

    target.on("dialog", lambda d: (print(f"[다이얼로그] {d.type} {d.message!r}"), d.accept()))

    btn = target.locator("#btn_excel_export")
    print(f"[버튼 존재] {btn.count()} visible={btn.is_visible()} enabled={btn.is_enabled()}")
    box = btn.bounding_box()
    print(f"[버튼 위치] {box}")

    try:
        with target.expect_download(timeout=15000) as dl_info:
            btn.click(force=True)
        download = dl_info.value
        suggested = download.suggested_filename
        dest = OUT_DIR / f"최상위수학라이트_중1_1학기_목록_{suggested}"
        download.save_as(str(dest))
        print(f"[다운로드 완료] {dest}")
    except Exception as e:
        print(f"[다운로드 이벤트 없음] {e}")
        print(f"[클릭 후 현재 탭 수] {len(context.pages)}")
        for i, pg in enumerate(context.pages):
            print(f"  [{i}] {pg.url}")
