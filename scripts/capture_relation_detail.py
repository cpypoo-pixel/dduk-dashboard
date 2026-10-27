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

    bodies = {}

    def on_response(res):
        url = res.url
        for key in ["main-list", "relation-list", "main-info"]:
            if key in url and key not in bodies:
                try:
                    bodies[key] = {"url": url, "json": res.json()}
                except Exception as e:
                    bodies[key] = {"url": url, "err": str(e)}

    target.on("response", on_response)

    search_box = target.locator("input[placeholder*='교재'], input[placeholder*='입력']").first
    search_box.click(force=True)
    search_box.fill("")
    target.keyboard.type("중1 1학기 2022개정 수학 최상위수학 라이트", delay=80)
    target.wait_for_timeout(1500)
    option = target.locator("text=중1 1학기 2022개정 수학 최상위수학 라이트").first
    if option.count() > 0:
        option.click(force=True)
        target.wait_for_timeout(500)
    target.mouse.click(835, 70)
    target.wait_for_timeout(2500)

    for key, val in bodies.items():
        print(f"=== {key} ===")
        print("url:", val["url"])
        if "json" in val:
            j = val["json"]
            s = json.dumps(j, ensure_ascii=False)
            print(s[:2500])
        else:
            print("err:", val["err"])
        print()

    with open(r"D:\ddddashboard\data\api_sample_bodies.json", "w", encoding="utf-8") as f:
        json.dump({k: v.get("json") for k, v in bodies.items()}, f, ensure_ascii=False, indent=2)
    print("저장 완료")
