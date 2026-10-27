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
    page.wait_for_timeout(500)

    page.evaluate("window.scrollTo(0, 1800)")
    page.wait_for_timeout(1000)
    page.screenshot(path=r"D:\ddddashboard\data\dashboard_check2.png")

    page.evaluate("window.scrollTo(0, 3600)")
    page.wait_for_timeout(1000)
    page.screenshot(path=r"D:\ddddashboard\data\dashboard_check3.png")

    page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
    page.wait_for_timeout(1000)
    page.screenshot(path=r"D:\ddddashboard\data\dashboard_check4.png")
    print("완료", page.evaluate("document.body.scrollHeight"))
