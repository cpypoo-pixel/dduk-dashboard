# -*- coding: utf-8 -*-
"""여러 book-item-edit 탭 중 '최상위수학 라이트'가 선택된 탭을 찾는다. 조회만 수행."""
import sys
from playwright.sync_api import sync_playwright

sys.stdout.reconfigure(encoding="utf-8")

CDP_URL = "http://localhost:9333"

with sync_playwright() as p:
    browser = p.chromium.connect_over_cdp(CDP_URL)
    context = browser.contexts[0]
    for i, pg in enumerate(context.pages):
        if "book-item-edit" not in pg.url:
            continue
        try:
            total_text = pg.locator("text=/총\\s*\\d+\\s*건/").first.inner_text(timeout=2000)
        except Exception:
            total_text = "N/A"
        try:
            sel_text = pg.locator("#sltBook, select").first.input_value(timeout=1000)
        except Exception:
            sel_text = None
        print(f"[tab {i}] total={total_text!r} sel_value={sel_text!r}")
