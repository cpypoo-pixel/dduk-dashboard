# -*- coding: utf-8 -*-
"""'교재관리' 등 교재 목록을 보여주는 화면을 탐색한다. 조회만 수행."""
import sys
sys.stdout.reconfigure(encoding="utf-8")
from playwright.sync_api import sync_playwright

CDP_URL = "http://localhost:9333"

with sync_playwright() as p:
    browser = p.chromium.connect_over_cdp(CDP_URL)
    context = browser.contexts[0]
    print(f"[열린 탭 수] {len(context.pages)}")
    for i, pg in enumerate(context.pages):
        print(f"  [{i}] {pg.url}")

    # booklist 탭에서 메뉴 구조 확인
    target = None
    for pg in context.pages:
        if "odapnote.t-ime.com" in pg.url:
            target = pg
            break
    if target:
        target.bring_to_front()
        target.wait_for_timeout(500)
        menu_text = target.evaluate(
            """
            () => {
              const links = [...document.querySelectorAll('a, button')];
              return links
                .filter(el => el.offsetParent !== null)
                .map(el => ({ text: (el.innerText||'').trim(), href: el.getAttribute('href') }))
                .filter(x => x.text);
            }
            """
        )
        for m in menu_text[:60]:
            print(m)
