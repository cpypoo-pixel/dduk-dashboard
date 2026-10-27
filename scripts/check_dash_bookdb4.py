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
    page.evaluate("""() => {
        const el = document.querySelector('[data-testid="stMain"]') || document.querySelector('section.main');
        if (el) el.scrollTo(0, el.scrollHeight);
    }""")
    page.wait_for_timeout(1500)
    page.screenshot(path=r"D:\ddddashboard\data\dash_bookdb_bottom.png")
    print("완료")
