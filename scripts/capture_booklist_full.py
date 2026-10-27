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

    result = {}

    def on_response(res):
        if "book-item-edit/book-list" in res.url:
            try:
                result["resp"] = res.json()
            except Exception as e:
                result["err"] = str(e)

    target.on("response", on_response)
    target.reload(wait_until="networkidle", timeout=30000)
    target.wait_for_timeout(2000)

    resp = result.get("resp")
    books = resp["data"]["bookList"]
    print("전체 교재 수:", len(books))
    print(json.dumps(books[0], ensure_ascii=False, indent=2))
    print()
    print("---두번째---")
    print(json.dumps(books[1], ensure_ascii=False, indent=2))

    with open(r"D:\ddddashboard\data\booklist_api_raw.json", "w", encoding="utf-8") as f:
        json.dump(resp, f, ensure_ascii=False, indent=2)
    print("\n저장 완료: data/booklist_api_raw.json")
