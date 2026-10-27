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
    target.wait_for_timeout(500)

    selects = target.locator("select").all()
    rev_select = None
    for s in selects:
        opts = s.locator("option").all_inner_texts()
        if "2015개정" in opts:
            rev_select = s
            break

    rev_select.select_option(label="2015개정")
    target.wait_for_timeout(2000)
    body_text = target.locator("body").inner_text()
    m = re.search(r"\d+-\d+ of \d+", body_text)
    print("2015개정 선택 후:", m.group(0) if m else "못찾음")
    first_row = target.locator("table tr").nth(1).inner_text()
    print("첫 행:", first_row[:100])

    # 돋보기(검색) 버튼이 있는지 확인하고 클릭 시도
    search_btn = target.locator("button:has(svg), button.search, [class*=search]")
    print("검색버튼 후보:", search_btn.count())
