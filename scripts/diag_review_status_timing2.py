# -*- coding: utf-8 -*-
"""실제 프로젝트의 extract_field()를 그대로 사용해 '문항검수' 값이 시간에 따라 바뀌는지 확인.
조회만 수행."""
import sys
sys.path.insert(0, r"D:\ddddashboard\scripts")
sys.stdout.reconfigure(encoding="utf-8")

from playwright.sync_api import sync_playwright
import step5_batch_cdp as mod

CDP_URL = "http://localhost:9333"

with sync_playwright() as p:
    browser = p.chromium.connect_over_cdp(CDP_URL)
    context = browser.contexts[0]
    target = None
    for pg in context.pages:
        if "book-item-edit" in pg.url:
            target = pg
    target.bring_to_front()
    vp = target.evaluate("() => ({w: window.innerWidth, h: window.innerHeight})")
    mod.VIEWPORT["w"] = vp["w"]
    mod.VIEWPORT["h"] = vp["h"]
    print("viewport:", vp)

    for i in range(8):
        code = mod.extract_field(target, "문제코드")
        review = mod.extract_field(target, "문항검수")
        print(f"[{i}] 문제코드={code!r} 문항검수={review!r}")
        target.wait_for_timeout(800)
