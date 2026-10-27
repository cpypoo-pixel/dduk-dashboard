# -*- coding: utf-8 -*-
import sys, json
sys.stdout.reconfigure(encoding="utf-8")
from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.connect_over_cdp("http://localhost:9333")
    context = browser.contexts[0]
    target = None
    for pg in context.pages:
        if "book-item-edit" in pg.url:
            target = pg
    target.bring_to_front()

    headers_captured = {}

    def on_req(req):
        if "main-list" in req.url and "main-list" not in headers_captured:
            headers_captured["main-list"] = req.all_headers()
        if "relation-list" in req.url and "relation-list" not in headers_captured:
            headers_captured["relation-list"] = req.all_headers()

    target.on("request", on_req)

    search_box = target.locator("input[placeholder*='교재'], input[placeholder*='입력']").first
    search_box.click(force=True)
    search_box.fill("")
    target.keyboard.type("중1 1학기 2022개정 수학 최상위수학 라이트", delay=80)
    target.wait_for_timeout(1500)
    option = target.locator("text=중1 1학기 2022개정 수학 최상위수학 라이트").first
    if option.count() > 0:
        option.click(force=True)
        target.wait_for_timeout(500)
    target.mouse.click(835, 70)
    target.wait_for_timeout(2500)

    for k, v in headers_captured.items():
        print(f"=== {k} ===")
        print(json.dumps(v, ensure_ascii=False, indent=2))
