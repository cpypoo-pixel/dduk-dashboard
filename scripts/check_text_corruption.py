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

    texts = page.evaluate(
        """
        () => {
          const svgTexts = [...document.querySelectorAll('.gtitle, .g-xtitle, .ytitle')];
          return svgTexts.map(t => t.textContent);
        }
        """
    )
    for t in texts:
        print(repr(t))
