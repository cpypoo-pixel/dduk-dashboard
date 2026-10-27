"""우측 상단 녹색 엑셀 버튼으로 추정되는 요소를 CDP 연결 세션에서 진단한다.
조회만 수행하며 클릭/다운로드는 하지 않는다."""
from playwright.sync_api import sync_playwright

CDP_URL = "http://localhost:9333"

with sync_playwright() as p:
    browser = p.chromium.connect_over_cdp(CDP_URL)
    context = browser.contexts[0]
    print(f"[열린 탭 수] {len(context.pages)}")
    for i, pg in enumerate(context.pages):
        print(f"  [{i}] {pg.url}")
    # book-item-edit 페이지(문제편집기)를 우선 선택
    page = None
    for pg in context.pages:
        if "book-item-edit" in pg.url:
            page = pg
            break
    if page is None:
        page = context.pages[0] if context.pages else context.new_page()
    print(f"[현재 URL] {page.url}")

    # 화면 우측 상단(대략 x>1650, y<180) 영역의 클릭 가능한 요소를 모두 덤프
    info = page.evaluate(
        """
        () => {
          const results = [];
          const all = document.querySelectorAll('button, a, img, svg, i, [role="button"], [onclick]');
          for (const el of all) {
            const r = el.getBoundingClientRect();
            if (r.x > 1600 && r.y < 200 && r.width > 0 && r.height > 0) {
              results.push({
                tag: el.tagName,
                cls: el.className && el.className.toString ? el.className.toString() : el.className,
                id: el.id,
                title: el.title,
                alt: el.alt,
                text: (el.innerText || '').trim().slice(0, 30),
                x: r.x, y: r.y, w: r.width, h: r.height
              });
            }
          }
          return results;
        }
        """
    )
    for item in info:
        print(item)
