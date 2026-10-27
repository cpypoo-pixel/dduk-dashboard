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
    page.reload(wait_until="networkidle")
    page.wait_for_timeout(1500)

    def scroll_and_shot(y, name):
        page.evaluate(f"""
            () => {{
              const el = document.querySelector('[data-testid="stMain"]') || document.querySelector('section.main');
              if (el) el.scrollTo(0, {y});
            }}
        """)
        page.wait_for_timeout(800)
        page.screenshot(path=fr"D:\ddddashboard\data\{name}.png")

    scroll_and_shot(0, "d_top")
    scroll_and_shot(1800, "d_mid")
    scroll_and_shot(99999, "d_bottom")
    print("완료")
