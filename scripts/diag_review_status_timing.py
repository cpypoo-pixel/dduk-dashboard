# -*- coding: utf-8 -*-
"""현재 열려있는 항목(page=0160, q=0030, 엑셀상 문항검수=완료)의 우측 패널 '문항검수' 값이
시간이 지나면 바뀌는지(비동기 로딩 지연 여부) 확인. 조회만 수행, 클릭/저장 없음."""
import sys
from playwright.sync_api import sync_playwright

sys.stdout.reconfigure(encoding="utf-8")
CDP_URL = "http://localhost:9333"


def read_review_select(page):
    sel = page.locator("select").filter(has=page.locator("xpath=ancestor::tr[th[contains(text(),'문항검수')]]"))
    # 좀 더 단순하게: th 텍스트가 '문항검수'인 tr 안의 select
    tr = page.locator("xpath=//th[normalize-space(text())='문항검수']/ancestor::tr[1]")
    cnt = tr.count()
    if cnt == 0:
        return None, "tr not found"
    sel2 = tr.locator("select")
    if sel2.count() > 0:
        val = sel2.first.evaluate("el => ({value: el.value, text: el.options[el.selectedIndex] ? el.options[el.selectedIndex].text : null})")
        return val, "select"
    # select 아니면 텍스트
    return tr.first.inner_text(), "text"


with sync_playwright() as p:
    browser = p.chromium.connect_over_cdp(CDP_URL)
    context = browser.contexts[0]
    target = None
    for pg in context.pages:
        if "book-item-edit" in pg.url:
            target = pg
    target.bring_to_front()

    for i in range(6):
        val, kind = read_review_select(target)
        print(f"[{i} / t={i*1.0:.0f}s] kind={kind} val={val}")
        target.wait_for_timeout(1000)
