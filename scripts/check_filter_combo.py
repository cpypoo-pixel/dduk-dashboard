# -*- coding: utf-8 -*-
import sys
sys.stdout.reconfigure(encoding="utf-8")
from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.connect_over_cdp("http://localhost:9333")
    context = browser.contexts[0]
    page = None
    for pg in context.pages:
        if "localhost:8501" in pg.url:
            page = pg
    page.bring_to_front()
    page.wait_for_timeout(500)

    # 학교급 selectbox를 '고등'으로 변경
    sels = page.locator('[data-testid="stSelectbox"]')
    print("selectbox 개수:", sels.count())
    level_select = sels.nth(1)  # 자료유형(0), 학교급(1)
    level_select.click()
    page.wait_for_timeout(300)
    option = page.locator('li', has_text="고등").first
    option.click()
    page.wait_for_timeout(1500)
    page.screenshot(path=r"D:\ddddashboard\data\ui_filter_highschool.png")
    print("완료")
