# -*- coding: utf-8 -*-
"""교재 하나를 검색/선택할 때 호출되는 문항 목록 API를 캡처. 조회만 수행."""
import sys, json
sys.stdout.reconfigure(encoding="utf-8")
from playwright.sync_api import sync_playwright

TEXTBOOK_NAME = "중1 1학기 2022개정 수학 최상위수학 라이트"

with sync_playwright() as p:
    browser = p.chromium.connect_over_cdp("http://localhost:9333")
    context = browser.contexts[0]
    target = None
    for pg in context.pages:
        if "book-item-edit" in pg.url:
            target = pg
    target.bring_to_front()

    captured = []

    def on_response(res):
        req = res.request
        if req.resource_type in ("xhr", "fetch") and "mswitch.co.kr" in res.url:
            captured.append(res)

    target.on("response", on_response)

    # 검색창에 교재명 입력 (기존에 검증된 방식: 실제 키입력 + 자동완성 옵션 클릭)
    search_box = target.locator("input[placeholder*='교재'], input[placeholder*='입력']").first
    search_box.click(force=True)
    search_box.fill("")
    target.keyboard.type(TEXTBOOK_NAME, delay=80)
    target.wait_for_timeout(1500)

    option = target.locator(f"text={TEXTBOOK_NAME}").first
    if option.count() > 0:
        option.click(force=True)
        target.wait_for_timeout(500)

    # 검색(돋보기, 좌표 기반 - 기존 검증값)
    target.mouse.click(835, 70)
    target.wait_for_timeout(2500)

    print(f"[캡처된 요청 수] {len(captured)}")
    for res in captured:
        print(res.request.method, res.url, res.status)
