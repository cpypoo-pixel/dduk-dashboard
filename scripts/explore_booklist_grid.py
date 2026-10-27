# -*- coding: utf-8 -*-
"""booklist tui-grid의 실제 data-column-name 구조와 전체 건수/페이지네이션을 조회."""
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

    cols = target.evaluate(
        """
        () => {
          const cells = [...document.querySelectorAll('[data-column-name]')];
          const names = [...new Set(cells.map(c => c.getAttribute('data-column-name')))];
          return names;
        }
        """
    )
    print("data-column-name 목록:", cols)

    # 첫번째 row-key=0 의 모든 컬럼 값
    row0 = target.evaluate(
        """
        () => {
          const cells = [...document.querySelectorAll('[data-row-key="0"]')];
          return cells.map(c => ({col: c.getAttribute('data-column-name'), text: c.innerText.trim()}));
        }
        """
    )
    print("\nrow-key=0:", row0)

    # 페이지네이션/총건수 탐색
    pag = target.evaluate(
        """
        () => {
          const cand = [...document.querySelectorAll('*')].filter(el =>
            el.children.length === 0 && /\\d+\\s*(건|개)/.test(el.innerText || '')
          );
          return cand.slice(0, 10).map(e => e.innerText.trim());
        }
        """
    )
    print("\n건수 후보 텍스트:", pag)

    # 전체 row 개수(현재 로드된 것)
    total_rows = target.evaluate(
        "() => new Set([...document.querySelectorAll('[data-row-key]')].map(e=>e.getAttribute('data-row-key'))).size"
    )
    print("\n현재 로드된 고유 row-key 수:", total_rows)
