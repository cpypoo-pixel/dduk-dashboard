# -*- coding: utf-8 -*-
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

    result = target.evaluate(
        """
        async () => {
          const res = await fetch('/api/in/mnote-bank/book-item-edit/main-list?perPage=&book_id=391&item_filter=&del_yn=N&page=1',
            { headers: { 'X-Requested-With': 'XMLHttpRequest' } });
          const j = await res.json();
          return { count: j.data.contents.length, first: j.data.contents[0] };
        }
        """
    )
    print(result)
