# -*- coding: utf-8 -*-
"""book-item-edit 페이지를 새로고침하고, 교재 하나를 검색/선택하는 과정에서 호출되는
XHR/fetch 요청과 응답을 캡처한다. 조회만 수행(저장/수정 없음)."""
import sys, json
sys.stdout.reconfigure(encoding="utf-8")
from playwright.sync_api import sync_playwright

CDP_URL = "http://localhost:9333"
captured = []

with sync_playwright() as p:
    browser = p.chromium.connect_over_cdp(CDP_URL)
    context = browser.contexts[0]
    target = None
    for pg in context.pages:
        if "book-item-edit" in pg.url:
            target = pg
    target.bring_to_front()

    def on_response(res):
        req = res.request
        if req.resource_type in ("xhr", "fetch"):
            captured.append({"url": res.url, "method": req.method, "status": res.status})

    target.on("response", on_response)

    target.reload(wait_until="networkidle", timeout=30000)
    target.wait_for_timeout(2000)

    print(f"[새로고침 후 캡처된 요청 수] {len(captured)}")
    for c in captured:
        print(c)
