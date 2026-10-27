# -*- coding: utf-8 -*-
"""엑셀다운로드 모달에서 '목록' 라벨을 클릭하면 바로 다운로드가 시작됨(사용자 확인).
조회(다운로드)만 수행."""
import sys
from pathlib import Path
from playwright.sync_api import sync_playwright

sys.stdout.reconfigure(encoding="utf-8")
CDP_URL = "http://localhost:9333"
OUT_DIR = Path(r"D:\ddddashboard\data")

with sync_playwright() as p:
    browser = p.chromium.connect_over_cdp(CDP_URL)
    context = browser.contexts[0]
    target = None
    for pg in context.pages:
        if "book-item-edit" in pg.url:
            target = pg
    target.bring_to_front()

    # 모달이 닫혀있을 수 있으니 엑셀 버튼부터 다시 클릭해 모달을 연다
    excel_btn = target.locator("#btn_excel_export")
    if not target.locator("label[for='header_com_excel_export0']").is_visible():
        excel_btn.click(force=True)
        target.wait_for_timeout(1000)

    label = target.locator("label[for='header_com_excel_export0']")
    print("라벨 존재/표시:", label.count(), label.is_visible())

    try:
        with target.expect_download(timeout=20000) as dl_info:
            label.click()
        download = dl_info.value
        suggested = download.suggested_filename
        dest = OUT_DIR / f"최상위수학라이트_중1_1학기_목록_{suggested}"
        download.save_as(str(dest))
        print(f"[다운로드 완료] {dest}")
    except Exception as e:
        print(f"[실패] {e}")
        target.screenshot(path=str(OUT_DIR / "after_label_click.png"))
