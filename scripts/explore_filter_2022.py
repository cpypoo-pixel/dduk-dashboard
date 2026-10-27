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

    # 개정년도 select 찾기 (옵션에 '2022개정' 포함)
    selects = target.locator("select").all()
    rev_select = None
    for s in selects:
        opts = s.locator("option").all_inner_texts()
        if "2022개정" in opts:
            rev_select = s
            break
    print("개정년도 select 찾음:", rev_select is not None)
    rev_select.select_option(label="2022개정")
    target.wait_for_timeout(1500)

    body_text = target.locator("body").inner_text()
    import re
    m = re.search(r"\d+-\d+ of \d+", body_text)
    print("필터 후 범위 텍스트:", m.group(0) if m else "못찾음")

    # Rows per page 옵션 확인
    rpp = target.locator("text=Rows per page").locator("xpath=..")
    print(rpp.inner_text() if rpp.count() else "rows-per-page 영역 못찾음")

    target.screenshot(path=r"D:\ddddashboard\data\booklist_2022.png")
