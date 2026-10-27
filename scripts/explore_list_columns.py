# -*- coding: utf-8 -*-
"""문제 목록 그리드(좌측 리스트)에 쌍둥이 개수를 바로 보여주는 컬럼이 있는지 확인.
'...' 컬럼설정 버튼을 눌러서 숨겨진 컬럼 목록도 확인. 조회만 수행."""
import sys
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
    target.wait_for_timeout(500)

    # 현재 리스트 헤더들
    headers = target.evaluate(
        """
        () => {
          const ths = [...document.querySelectorAll('.tui-grid-cell-head, th')];
          return ths.map(t => t.innerText.trim()).filter(Boolean);
        }
        """
    )
    print("현재 보이는 헤더:", headers)

    # '전체문항' 드롭다운 옆 '...' 버튼 클릭해서 컬럼 설정 메뉴 확인
    more_btn = target.locator("text=...").first
    print("'...' 버튼 존재:", more_btn.count())
    if more_btn.count() > 0:
        more_btn.click(force=True)
        target.wait_for_timeout(500)
        target.screenshot(path=r"D:\ddddashboard\data\list_column_menu.png")
        print("스크린샷 저장")
