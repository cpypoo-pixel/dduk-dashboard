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
    val = rev_select.evaluate("el => el.value")
    print("현재 select value:", val)

    # 돋보기 아이콘 버튼 (교재명 검색창 옆)
    search_icon = target.locator('svg, i, button').filter(has_text="")
    # 검색 input 옆 버튼을 좌표로 클릭 시도 - 스크린샷에서 봤던 위치 근처
    box = target.locator("input[placeholder='검색을 해주세요']").bounding_box()
    print("검색창 위치:", box)
    if box:
        target.mouse.click(box["x"] + box["width"] + 20, box["y"] + box["height"]/2)
        target.wait_for_timeout(1500)
        body_text = target.locator("body").inner_text()
        m = re.search(r"\d+-\d+ of \d+", body_text)
        print("돋보기 클릭 후:", m.group(0) if m else "못찾음")
        first_row = target.locator("table tr").nth(1).inner_text()
        print("첫 행:", first_row[:120])
