# -*- coding: utf-8 -*-
"""엑셀 버튼 클릭 시 실제로 어떤 네트워크 요청/콘솔 에러가 발생하는지 조회만 수행하여 진단."""
import sys
from playwright.sync_api import sync_playwright

sys.stdout.reconfigure(encoding="utf-8")
CDP_URL = "http://localhost:9333"

with sync_playwright() as p:
    browser = p.chromium.connect_over_cdp(CDP_URL)
    context = browser.contexts[0]
    target = None
    for pg in context.pages:
        if "book-item-edit" in pg.url:
            target = pg
    target.bring_to_front()

    target.on("console", lambda m: print(f"[console:{m.type}] {m.text}"))
    target.on("pageerror", lambda e: print(f"[pageerror] {e}"))
    target.on("request", lambda r: print(f"[request] {r.method} {r.url}"))
    target.on("response", lambda r: print(f"[response] {r.status} {r.url}"))
    target.on("dialog", lambda d: (print(f"[dialog] {d.type} {d.message!r}"), d.accept()))
    target.on("popup", lambda p: print(f"[popup] {p.url}"))

    btn = target.locator("#btn_excel_export")
    print("[클릭 시작]")
    btn.click(force=True)
    target.wait_for_timeout(5000)
    print("[클릭 후 5초 대기 완료]")
