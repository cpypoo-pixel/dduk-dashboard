# -*- coding: utf-8 -*-
"""relation-list API를 반복 호출했을 때 속도를 측정. 조회만 수행."""
import sys, time, json
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

    H = "{ headers: { 'X-Requested-With': 'XMLHttpRequest' } }"

    # 먼저 main-list로 실제 존재하는 item_id 10개를 가져온다
    item_ids = target.evaluate(
        """
        async () => {
          const res = await fetch('/api/in/mnote-bank/book-item-edit/main-list?perPage=&book_id=13378&item_filter=&del_yn=N&page=1',
            { headers: { 'X-Requested-With': 'XMLHttpRequest' } });
          const j = await res.json();
          return j.data.contents.slice(0,10).map(c => c.item_id);
        }
        """
    )
    print("실제 item_id 10개:", item_ids)

    t0 = time.time()
    results = target.evaluate(
        """
        async (itemIds) => {
          const out = [];
          for (const id of itemIds) {
            const res = await fetch(`/api/in/mnote-bank/book-item-edit/relation-list?book_id=13378&item_id=${id}`,
              { headers: { 'X-Requested-With': 'XMLHttpRequest' } });
            const text = await res.text();
            let j;
            try { j = JSON.parse(text); } catch(e) { out.push({id, error: text.slice(0,100)}); continue; }
            out.push({id, count: (j.data && j.data.relationList) ? j.data.relationList.length : null});
          }
          return out;
        }
        """,
        item_ids,
    )
    t1 = time.time()
    print(f"10건 순차 호출 소요시간: {t1-t0:.2f}초 (건당 {(t1-t0)/10*1000:.0f}ms)")
    for r in results:
        print(r)
