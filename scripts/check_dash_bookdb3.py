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
    page.goto("http://localhost:8501/%EA%B5%90%EC%9E%AC_DB", wait_until="networkidle", timeout=20000)
    page.wait_for_timeout(2000)
    page.screenshot(path=r"D:\ddddashboard\data\dash_bookdb_top2.png")
    print("url:", page.url)
