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

    nav_links = page.evaluate(
        """
        () => [...document.querySelectorAll('a, [data-testid="stSidebarNavLink"]')]
          .filter(el => el.offsetParent !== null)
          .map(el => ({text: el.innerText.trim(), href: el.getAttribute('href')}))
        """
    )
    for n in nav_links:
        print(n)
