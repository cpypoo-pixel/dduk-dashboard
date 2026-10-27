# -*- coding: utf-8 -*-
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

    tables = target.locator("table")
    print("table 개수:", tables.count())
    for i in range(tables.count()):
        t = tables.nth(i)
        cls = t.get_attribute("class")
        rows = t.locator("tr").count()
        print(f"[table {i}] class={cls} rows={rows}")

    # 가장 row가 많은 테이블의 첫 2개 row HTML
    counts = [tables.nth(i).locator("tr").count() for i in range(tables.count())]
    best = counts.index(max(counts))
    print(f"\n가장 row 많은 테이블 index={best}")
    big = tables.nth(best)
    print(big.locator("tr").nth(0).inner_html()[:800])
    print("---")
    print(big.locator("tr").nth(1).inner_html()[:800])

    # 페이지네이션 요소
    pagin = target.locator(".pagination, [class*=pagin], [class*=paging]")
    print("\n페이지네이션 후보 개수:", pagin.count())
    if pagin.count() > 0:
        print(pagin.first.inner_text()[:300])
