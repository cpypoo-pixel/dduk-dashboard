# -*- coding: utf-8 -*-
"""book-list API의 요청 payload와 응답 본문 구조를 확인. 조회만 수행."""
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
            req = res.request
            try:
                result["req_body"] = req.post_data
            except Exception as e:
                result["req_body_err"] = str(e)
            try:
                body = res.json()
                result["resp"] = body
            except Exception as e:
                result["resp_err"] = str(e)

    target.on("response", on_response)
    target.reload(wait_until="networkidle", timeout=30000)
    target.wait_for_timeout(2000)

    print("요청 payload:", result.get("req_body"))
    resp = result.get("resp")
    if resp is not None:
        if isinstance(resp, dict):
            print("응답 최상위 키:", list(resp.keys()))
            for k, v in resp.items():
                if isinstance(v, list):
                    print(f"  {k}: list, 길이={len(v)}")
                    if v:
                        print(f"    첫 항목:", json.dumps(v[0], ensure_ascii=False)[:1000])
                else:
                    print(f"  {k}: {str(v)[:200]}")
        else:
            print("응답 타입:", type(resp), str(resp)[:500])
    else:
        print("응답 캡처 실패:", result.get("resp_err"))
