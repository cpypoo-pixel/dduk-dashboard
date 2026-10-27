# -*- coding: utf-8 -*-
"""STEP 6: textbook_items.csv(엑셀 원본, 신뢰 가능한 상태값)와 step5_all_items.csv(브라우저 수집,
엑셀에 없는 문제코드/등록정보/쌍둥이-유사문항 정보)를 병합해 최종 검증 데이터셋을 만든다."""
import sys
import pandas as pd

sys.stdout.reconfigure(encoding="utf-8")

BASE = pd.read_csv(r"D:\ddddashboard\data\textbook_items.csv", dtype=str)
SCRAPED = pd.read_csv(r"D:\ddddashboard\data\step5_all_items.csv", dtype=str)

BASE["key"] = BASE["page"].str.zfill(4) + "_" + BASE["question_number"].str.zfill(4)
SCRAPED["key"] = SCRAPED["page"].str.zfill(4) + "_" + SCRAPED["question_number"].str.zfill(4)

browser_only_cols = [
    "question_code", "registered_by", "registered_at", "modified_by", "modified_at",
    "tabs_present", "tabs_count", "review_blocks_detail",
]

merged = BASE.merge(SCRAPED[["key"] + browser_only_cols], on="key", how="left")

missing_browser = merged["question_code"].isna().sum()
print(f"[병합 결과] 총 {len(merged)}행, 브라우저 수집 데이터 누락 {missing_browser}건")

merged["data_status"] = merged["question_code"].apply(lambda v: "확인완료" if pd.notna(v) else "미확인")

# tabs_present (예: "원문항|쌍둥이 1번|쌍둥이 2번|...") 에서 쌍둥이/유사 문항 개수를 분리 집계
def count_tab_type(tabs_present, keyword):
    if pd.isna(tabs_present):
        return 0
    return sum(1 for t in tabs_present.split("|") if t.strip().startswith(keyword))

merged["twin_count"] = merged["tabs_present"].apply(lambda v: count_tab_type(v, "쌍둥이"))
merged["similar_count"] = merged["tabs_present"].apply(lambda v: count_tab_type(v, "유사"))

merged = merged.drop(columns=["key"])
out_path = r"D:\ddddashboard\data\final_items.csv"
merged.to_csv(out_path, index=False, encoding="utf-8-sig")
print(f"[저장] {out_path}")
print()
print("[data_status 분포]")
print(merged["data_status"].value_counts())
print()
print("[item_review_status 분포 (최종, 엑셀 기준)]")
print(merged["item_review_status"].value_counts())
print()
print("[문제삭제(deleted) 분포]")
print(merged["deleted"].value_counts())
print()
print("[tabs_count 분포]")
print(merged["tabs_count"].value_counts(dropna=False).sort_index())
print()
print("[twin_count(쌍둥이 개수) 분포]")
print(merged["twin_count"].value_counts(dropna=False).sort_index())
print(f"[쌍둥이 문항 총합] {merged['twin_count'].sum()}개 (원문항 {len(merged)}개 기준)")
print()
print("[similar_count(유사 개수) 분포]")
print(merged["similar_count"].value_counts(dropna=False).sort_index())
