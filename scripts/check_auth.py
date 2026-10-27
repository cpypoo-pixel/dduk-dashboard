# -*- coding: utf-8 -*-
import sys
sys.stdout.reconfigure(encoding="utf-8")
from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.connect_over_cdp("http://localhost:9333")
    context = browser.contexts[0]
    page = context.new_page()
    page.goto("http://localhost:8501", wait_until="networkidle", timeout=20000)
    page.wait_for_timeout(1500)
    page.screenshot(path=r"D:\ddddashboard\data\auth_before.png")
    print("로그인 전 스크린샷 저장")

    pw_input = page.locator('input[type="password"]')
    pw_input.fill("eoqkrskwk")
    page.locator("button", has_text="입장").click()
    page.wait_for_timeout(2000)
    page.screenshot(path=r"D:\ddddashboard\data\auth_after.png")
    print("로그인 후 스크린샷 저장")
