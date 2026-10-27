# -*- coding: utf-8 -*-
import sys
sys.stdout.reconfigure(encoding="utf-8")
from playwright.sync_api import sync_playwright
import re

with sync_playwright() as p:
    browser = p.chromium.connect_over_cdp("http://localhost:9333")
    context = browser.contexts[0]
    target = None
    for pg in context.pages:
        if pg.url.endswith("/booklist"):
            target = pg
    target.bring_to_front()

    info = target.evaluate(
        """
        () => {
          const input = document.querySelector('input[placeholder="검색을 해주세요"]');
          const parent = input.closest('div');
          const siblings = [...parent.parentElement.querySelectorAll('*')].filter(el => el.children.length===0);
          return siblings.map(el => {
            const r = el.getBoundingClientRect();
            return {tag: el.tagName, cls: el.className, x: r.x, y: r.y, w: r.width, h: r.height};
          });
        }
        """
    )
    for i in info:
        print(i)
