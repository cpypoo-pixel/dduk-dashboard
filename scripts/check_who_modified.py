# -*- coding: utf-8 -*-
"""의심되는 6개 문항의 main-info를 조회해서 수정자(upt_mem_info)와 수정일시를 확인.
조회만 수행."""
import sys, json
sys.stdout.reconfigure(encoding="utf-8")
from playwright.sync_api import sync_playwright
import pandas as pd

items = pd.read_csv(r"D:\ddddashboard\data\step8_all_items.csv", dtype=str)
book = items[items["book_id"] == "13378"]
known_pending = [("0037","0009"),("0040","0021"),("0047","0006"),("0051","0026"),("0058","0062"),("0066","0021")]
item_ids = []
for page, num in known_pending:
    row = book[(book["page"]==page) & (book["item_num"]==num)]
    item_ids.append(row.iloc[0]["item_id"])
print("확인할 item_id:", item_ids)

with sync_playwright() as p:
    browser = p.chromium.connect_over_cdp("http://localhost:9333")
    context = browser.contexts[0]
    target = None
    for pg in context.pages:
        if "book-item-edit" in pg.url:
            target = pg
    target.bring_to_front()

    results = target.evaluate(
        """
        async (itemIds) => {
          const out = [];
          for (const id of itemIds) {
            const res = await fetch(`/api/in/mnote-bank/book-item-edit/main-info?book_id=13378&item_id=${id}`,
              { headers: { 'X-Requested-With': 'XMLHttpRequest' } });
            const j = await res.json();
            const sub = j.data.subInfo;
            out.push({
              item_id: id,
              is_review_status: sub.is_review_status,
              upt_date: sub.upt_date,
              upt_mem_info: sub.upt_mem_info,
              reg_mem_info: sub.reg_mem_info,
              reg_date: sub.reg_date
            });
          }
          return out;
        }
        """,
        item_ids,
    )
    for r in results:
        print(json.dumps(r, ensure_ascii=False))
