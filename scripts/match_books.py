# -*- coding: utf-8 -*-
"""master 검수 리스트 엑셀(22개정 교재 551종)을 book-list API 결과(book_nm)와 매칭해 book_id를 찾는다."""
import sys, json
sys.stdout.reconfigure(encoding="utf-8")
import pandas as pd

with open(r"D:\ddddashboard\data\booklist_api_raw.json", encoding="utf-8") as f:
    d = json.load(f)
books = d["data"]["bookList"]
name_to_books = {}
for b in books:
    name_to_books.setdefault(b["book_nm"], []).append(b)

xls = pd.ExcelFile(r"D:\ddddashboard\data\텍스트 검수 리스트.xlsx")
targets = []
for s in ["1. 고등시중교재", "3. 중등시중교재", "6. 표준교재"]:
    df = pd.read_excel(xls, sheet_name=s)
    df = df.dropna(subset=["교재명/시험지명"])
    df = df[df["교재명/시험지명"].str.contains("2022개정", na=False)]
    for _, row in df.iterrows():
        targets.append({
            "sheet": s,
            "name": row["교재명/시험지명"].strip(),
            "excel_item_count": row.get("문제수"),
        })

print(f"대상 교재 수: {len(targets)}")

matched = []
unmatched = []
for t in targets:
    cands = name_to_books.get(t["name"])
    if cands and len(cands) == 1:
        t["book_id"] = cands[0]["book_id"]
        t["is_review_complete"] = cands[0]["is_review_complete"]
        matched.append(t)
    elif cands and len(cands) > 1:
        t["candidates"] = cands
        unmatched.append(t)
    else:
        unmatched.append(t)

print(f"정확히 매칭: {len(matched)}")
print(f"매칭 실패/중복: {len(unmatched)}")
print()
print("매칭 실패 예시 (최대 20개):")
for u in unmatched[:20]:
    print(" ", u["name"], "| 후보수:", len(u.get("candidates", [])))

with open(r"D:\ddddashboard\data\book_match_result.json", "w", encoding="utf-8") as f:
    json.dump({"matched": matched, "unmatched": unmatched}, f, ensure_ascii=False, indent=2)
print("\n저장: data/book_match_result.json")
