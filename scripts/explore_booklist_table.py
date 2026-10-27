# -*- coding: utf-8 -*-
"""booklist 페이지의 테이블 헤더와 필터 옵션, '내신 등록하기' 버튼 동작을 조회만으로 확인."""
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
    target.wait_for_timeout(500)

    # 헤더
    headers = target.evaluate(
        """
        () => {
          const ths = [...document.querySelectorAll('thead th, .tui-grid-cell-header')];
          return ths.map(t => t.innerText.trim()).filter(Boolean);
        }
        """
    )
    print("헤더 후보:", headers)

    # 필터/드롭다운 옵션들
    selects = target.locator("select").all()
    print(f"\nselect 개수: {len(selects)}")
    for i, s in enumerate(selects):
        try:
            opts = s.locator("option").all_inner_texts()
            name = s.get_attribute("name") or s.get_attribute("id") or ""
            print(f"  [{i}] name/id={name} options={opts[:15]}")
        except Exception as e:
            print(f"  [{i}] 오류 {e}")

    # 총 교재 수(페이지네이션/카운트 표시)
    body_text = target.locator("body").inner_text()
    import re
    m = re.findall(r"총\s*\d+\s*건", body_text)
    print("\n'총 N건' 패턴:", m)
