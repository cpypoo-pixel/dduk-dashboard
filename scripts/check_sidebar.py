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
    page.goto("http://localhost:8501", wait_until="networkidle")
    page.wait_for_timeout(1500)

    links = page.evaluate(
        """
        () => [...document.querySelectorAll('[data-testid="stSidebarNav"] a, nav a')]
          .map(el => ({text: el.innerText, href: el.getAttribute('href')}))
        """
    )
    print("sidebar links:", links)

    html = page.evaluate("() => { const n = document.querySelector('[data-testid=\"stSidebarNav\"]'); return n ? n.outerHTML.slice(0,1500) : 'NOT FOUND'; }")
    print(html)
