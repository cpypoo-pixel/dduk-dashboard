# -*- coding: utf-8 -*-
import sys, json
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

    with open(r"D:\ddddashboard\data\book_match_result.json", encoding="utf-8") as f:
        match = json.load(f)
    # 큰 책 하나 찾기 (문제수 많은 것)
    biggest = max(match["matched"], key=lambda x: x.get("excel_item_count") or 0)
    print("가장 큰 교재:", biggest["name"], "엑셀 문제수:", biggest["excel_item_count"], "book_id:", biggest["book_id"])

    result = target.evaluate(
        """
        async (bookId) => {
          const res = await fetch(`/api/in/mnote-bank/book-item-edit/main-list?perPage=&book_id=${bookId}&item_filter=&del_yn=N&page=1`,
            { headers: { 'X-Requested-With': 'XMLHttpRequest' } });
          const j = await res.json();
          return { pagination: j.data.pagination, count: j.data.contents.length };
        }
        """,
        biggest["book_id"],
    )
    print("결과:", result)

    # 알려진 564건 교재(13378)로도 확인
    result2 = target.evaluate(
        """
        async () => {
          const res = await fetch(`/api/in/mnote-bank/book-item-edit/main-list?perPage=&book_id=13378&item_filter=&del_yn=N&page=1`,
            { headers: { 'X-Requested-With': 'XMLHttpRequest' } });
          const j = await res.json();
          return { pagination: j.data.pagination, count: j.data.contents.length };
        }
        """
    )
    print("13378(최상위수학 라이트, 기대값 564):", result2)
