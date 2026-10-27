# -*- coding: utf-8 -*-
import sys
from playwright.sync_api import sync_playwright

sys.stdout.reconfigure(encoding="utf-8")
CDP_URL = "http://localhost:9333"
OUT_DIR = r"D:\ddddashboard\data"

with sync_playwright() as p:
    browser = p.chromium.connect_over_cdp(CDP_URL)
    context = browser.contexts[0]
    target = None
    for pg in context.pages:
        if "book-item-edit" in pg.url:
            target = pg
    target.bring_to_front()

    target.on("dialog", lambda d: (print(f"[dialog] {d.type} {d.message!r}"), d.accept()))

    radio = target.locator("#header_com_excel_export0")
    print("라디오 존재:", radio.count())
    radio.evaluate("el => { el.checked = true; el.dispatchEvent(new Event('change', {bubbles:true})); el.dispatchEvent(new Event('click', {bubbles:true})); }")
    target.wait_for_timeout(500)
    target.screenshot(path=OUT_DIR + r"\after_radio_select.png")

    # 모달 전체 버튼 텍스트 나열
    btns = target.locator(".modal_body, .modal_footer, .frame-scroll-box").all()
    for b in btns:
        try:
            print("---블록---")
            print(b.inner_text()[:500])
        except Exception as e:
            print("err", e)

    all_btns = target.locator("button, .btn, a.btn, [class*=download]").all()
    for b in all_btns:
        try:
            if b.is_visible():
                box = b.bounding_box()
                if box and box["y"] > 300 and box["y"] < 700:
                    print("버튼후보:", b.inner_text()[:30], box)
        except Exception:
            pass
