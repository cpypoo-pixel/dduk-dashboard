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
    target.wait_for_timeout(4000)
    target.screenshot(path=r"D:\ddddashboard\data\after_excel_click2.png")
    html = target.locator("body").inner_html()
    # 모달 관련 텍스트만 추출
    import re
    m = re.search(r"엑셀\s*다운로드.{0,2000}", html, re.S)
    print(m.group(0)[:1500] if m else "모달 텍스트 없음")
