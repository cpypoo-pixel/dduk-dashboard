# -*- coding: utf-8 -*-
import sys
sys.stdout.reconfigure(encoding="utf-8")
from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.connect_over_cdp("http://localhost:9333")
    context = browser.contexts[0]
    page = None
    for pg in context.pages:
        if "localhost:8501" in pg.url:
            page = pg
    page.bring_to_front()
    page.goto("http://localhost:8501", wait_until="networkidle", timeout=20000)
    page.wait_for_timeout(2500)

    info = page.evaluate(
        """
        () => {
          const els = [...document.querySelectorAll('svg text')].filter(t => t.textContent.includes('문항'));
          return els.map(e => ({
            text: e.textContent,
            fontFamily: getComputedStyle(e).fontFamily,
          }));
        }
        """
    )
    for i in info:
        print(i)

    # 실제 사용 가능한 한글 폰트 확인
    fonts_check = page.evaluate(
        """
        async () => {
          const candidates = ['Malgun Gothic', 'Apple SD Gothic Neo', 'Noto Sans KR', 'Arial', 'sans-serif'];
          const results = {};
          for (const f of candidates) {
            results[f] = document.fonts.check(`16px "${f}"`);
          }
          return results;
        }
        """
    )
    print("폰트 사용가능여부:", fonts_check)
