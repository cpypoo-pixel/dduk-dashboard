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

    page.goto("http://localhost:8501", wait_until="networkidle", timeout=20000)
    page.wait_for_timeout(1500)
    page.screenshot(path=r"D:\ddddashboard\data\final_app_top.png")
    print("app top 저장")

    page.goto("http://localhost:8501/%EB%82%B4%EC%8B%A0_%EC%8B%9C%ED%97%98%EC%A7%80_DB", wait_until="networkidle", timeout=20000)
    page.wait_for_timeout(1500)
    page.screenshot(path=r"D:\ddddashboard\data\final_exam_top.png")
    print("exam top 저장, url=", page.url)
