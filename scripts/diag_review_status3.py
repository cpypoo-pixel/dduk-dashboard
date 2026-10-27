# -*- coding: utf-8 -*-
"""extract_field 로직을 그대로 복사해 '문항검수' 후보들을 전부 덤프. 조회만 수행, import 없음(부작용 방지)."""
import sys
sys.stdout.reconfigure(encoding="utf-8")
from playwright.sync_api import sync_playwright

CDP_URL = "http://localhost:9333"

with sync_playwright() as p:
    browser = p.chromium.connect_over_cdp(CDP_URL)
    context = browser.contexts[0]
    target = None
    for pg in context.pages:
        if "book-item-edit" in pg.url:
            target = pg
    target.bring_to_front()
    vp = target.evaluate("() => ({w: window.innerWidth, h: window.innerHeight})")
    print("viewport:", vp)

    label = "문항검수"
    candidates = target.get_by_text(label, exact=True).all()
    x_min = vp["w"] * 0.80
    y_min = vp["h"] * 0.12
    y_max = vp["h"] * 0.97
    print(f"경계: x>={x_min:.0f} y={y_min:.0f}-{y_max:.0f}")
    for ci, cand in enumerate(candidates):
        vis = cand.is_visible()
        box = cand.bounding_box()
        in_bounds = False
        if box:
            in_bounds = not (box["x"] < x_min or box["y"] < y_min or box["y"] > y_max)
        is_grid = cand.evaluate(
            "el => { let c = el; for (let i=0;i<8 && c;i++){ if (c.className && typeof c.className==='string' && c.className.includes('tui-grid')) return true; c = c.parentElement; } return false; }"
        )
        print(f"[{ci}] visible={vis} box={box} in_bounds={in_bounds} is_grid={is_grid}")
        if vis and box and in_bounds and not is_grid:
            row = cand.locator("xpath=ancestor::tr[1]")
            if row.count() == 0:
                row = cand.locator("xpath=..")
            print("    row html:", row.first.evaluate("el => el.outerHTML")[:500])
