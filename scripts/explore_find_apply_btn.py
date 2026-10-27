# -*- coding: utf-8 -*-
import sys
sys.stdout.reconfigure(encoding="utf-8")
from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.connect_over_cdp("http://localhost:9333")
    context = browser.contexts[0]
    target = None
    for pg in context.pages:
        if pg.url.endswith("/booklist"):
            target = pg
    target.bring_to_front()

    btns = target.evaluate(
        """
        () => {
          const els = [...document.querySelectorAll('button, a, [role=button], i, span')];
          return els.filter(el => el.offsetParent !== null).map(el => {
            const r = el.getBoundingClientRect();
            return {tag: el.tagName, cls: el.className, text: (el.innerText||'').trim().slice(0,20), x:r.x, y:r.y, w:r.width, h:r.height};
          }).filter(e => e.y < 120 && e.y > 0);
        }
        """
    )
    for b in btns:
        print(b)
