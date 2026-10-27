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
    target.wait_for_timeout(500)
    target.screenshot(path=r"D:\ddddashboard\data\booklist_full.png", full_page=True)
    print("스크린샷 저장")

    # body 전체 텍스트에서 숫자+건/페이지 관련 패턴
    body_text = target.locator("body").inner_text()
    import re
    for pat in [r"\d+\s*/\s*\d+", r"전체\s*\d+", r"총\s*\d+", r"페이지"]:
        found = re.findall(pat, body_text)
        if found:
            print(pat, "->", found[:10])
