# -*- coding: utf-8 -*-
import sys
sys.stdout.reconfigure(encoding="utf-8")
from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.connect_over_cdp("http://localhost:9333")
    context = browser.contexts[0]
    page = None
    for pg in context.pages:
        if "localhost:8501" in pg.url:
            page = pg
    page.bring_to_front()
    # 사이드바에서 '교재 DB' 링크 클릭
    link = page.locator("text=교재 DB").first
    if link.count() > 0:
        link.click(force=True)
        page.wait_for_timeout(2000)
    page.screenshot(path=r"D:\ddddashboard\data\dash_bookdb_top.png")
    print("완료")
