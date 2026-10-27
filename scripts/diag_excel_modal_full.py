# -*- coding: utf-8 -*-
import sys
from playwright.sync_api import sync_playwright

sys.stdout.reconfigure(encoding="utf-8")
CDP_URL = "http://localhost:9333"

with sync_playwright() as p:
    browser = p.chromium.connect_over_cdp(CDP_URL)
    context = browser.contexts[0]
    target = None
    for pg in context.pages:
        if "book-item-edit" in pg.url:
            target = pg
    target.bring_to_front()

    html = target.evaluate(
        """
        () => {
          const heading = [...document.querySelectorAll('h2')].find(h => h.textContent.includes('엑셀 다운로드'));
          if (!heading) return 'heading not found';
          let modal = heading;
          for (let i=0;i<6 && modal;i++) {
            if (modal.classList && (modal.classList.contains('modal') || modal.classList.contains('popup') || modal.id.toLowerCase().includes('modal') || modal.id.toLowerCase().includes('popup'))) break;
            modal = modal.parentElement;
          }
          return modal ? modal.outerHTML : 'modal container not found';
        }
        """
    )
    print(html[:6000])
