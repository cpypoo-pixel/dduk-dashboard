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

    target.on("request", lambda r: print(f"[req] {r.method} {r.url}") if r.resource_type in ("xhr", "fetch") else None)
    target.on("response", lambda r: print(f"[res] {r.status} {r.url}") if r.request.resource_type in ("xhr", "fetch") else None)

    icon = target.locator("i.split.searchGrey").locator("xpath=ancestor::button[1]")
    print("button count:", icon.count())
    icon.first.click(force=True)
    target.wait_for_timeout(2500)
    print("완료")
