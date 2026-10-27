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
    page.goto("http://localhost:8501", wait_until="networkidle", timeout=20000)
    page.wait_for_timeout(2500)

    all_texts = page.evaluate("() => document.querySelectorAll('svg text').length")
    print("svg text 개수:", all_texts)

    texts = page.evaluate(
        """
        () => [...document.querySelectorAll('svg text')].map(t => t.textContent).filter(t => t && t.trim())
        """
    )
    for t in texts:
        if "분" in t or "문" in t or "교" in t or "항" in t:
            print(repr(t))
