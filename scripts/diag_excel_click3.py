# -*- coding: utf-8 -*-
import sys
from playwright.sync_api import sync_playwright

sys.stdout.reconfigure(encoding="utf-8")
CDP_URL = "http://localhost:9333"

with sync_playwright() as p:
    browser = p.chromium.connect_over_cdp(CDP_URL)
    context = browser.contexts[0]
    target = None
    for pg in context.pages:
        if "book-item-edit" in pg.url:
            target = pg
    target.bring_to_front()
    target.wait_for_timeout(500)

    btn = target.locator("#btn_excel_export")
    btn.click(force=True)
    target.wait_for_timeout(1500)
    target.screenshot(path=r"D:\ddddashboard\data\after_excel_click.png")
    print("스크린샷 저장 완료")
