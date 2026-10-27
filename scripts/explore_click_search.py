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

    icon = target.locator("i.split.searchGrey")
    print("아이콘 개수:", icon.count())
    icon.first.click()
    target.wait_for_timeout(1500)
    body_text = target.locator("body").inner_text()
    m = re.search(r"\d+-\d+ of \d+", body_text)
    print("검색 클릭 후:", m.group(0) if m else "못찾음")
    first_row = target.locator("table tr").nth(1).inner_text()
    print("첫 행:", first_row[:150])
