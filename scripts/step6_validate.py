# -*- coding: utf-8 -*-
"""STEP 6: 목록_최상위수학라이트.xlsx(관리페이지 원본) vs step5_all_items.csv(수집 데이터) 비교 검증.
수정/삭제 없이 조회 결과만 비교한다."""
import sys
import pandas as pd

sys.stdout.reconfigure(encoding="utf-8")

EXCEL_PATH = r"D:\ddddashboard\data\목록_최상위수학라이트.xlsx"
CSV_PATH = r"D:\ddddashboard\data\step5_all_items.csv"

excel = pd.read_excel(EXCEL_PATH)
csv = pd.read_csv(CSV_PATH, dtype=str)

print(f"[엑셀] {excel.shape[0]}행 / [수집 CSV] {csv.shape[0]}행")

# 키 정규화: 페이지, 문제번호를 4자리 0패딩 문자열로
excel["page_key"] = excel["페이지"].astype(int).astype(str).str.zfill(4)
excel["qno_key"] = excel["문제번호"].astype(int).astype(str).str.zfill(4)
excel["key"] = excel["page_key"] + "_" + excel["qno_key"]

csv["page_key"] = csv["page"].astype(str).str.zfill(4)
csv["qno_key"] = csv["question_number"].astype(str).str.zfill(4)
csv["key"] = csv["page_key"] + "_" + csv["qno_key"]

excel_keys = set(excel["key"])
csv_keys = set(csv["key"])

only_in_excel = excel_keys - csv_keys
only_in_csv = csv_keys - excel_keys

print(f"[엑셀에만 있음] {len(only_in_excel)}건")
if only_in_excel:
    print("  ", sorted(only_in_excel)[:20])
print(f"[수집 CSV에만 있음] {len(only_in_csv)}건")
if only_in_csv:
    print("  ", sorted(only_in_csv)[:20])

excel_dup = excel["key"].duplicated().sum()
csv_dup = csv["key"].duplicated().sum()
print(f"[엑셀 key 중복] {excel_dup}건 / [CSV key 중복] {csv_dup}건")

# 필드값 비교 (공통 key만)
common = sorted(excel_keys & csv_keys)
excel_idx = excel.set_index("key")
csv_idx = csv.set_index("key")

field_map = {
    "문항검수": "item_review_status",
    "텍스트변환": "text_conversion_status",
    "난이도": "difficulty",
    "문제종류": "question_type",
    "문제삭제": "deleted",
}

mismatch_counts = {k: 0 for k in field_map}
mismatch_examples = {k: [] for k in field_map}

for key in common:
    erow = excel_idx.loc[key]
    crow = csv_idx.loc[key]
    for ecol, ccol in field_map.items():
        ev = str(erow[ecol]).strip()
        cv = str(crow[ccol]).strip()
        if ev != cv:
            mismatch_counts[ecol] += 1
            if len(mismatch_examples[ecol]) < 5:
                mismatch_examples[ecol].append((key, ev, cv))

print()
print("[필드별 불일치 건수] (엑셀 vs 수집 CSV)")
for ecol, ccol in field_map.items():
    print(f"  {ecol} <-> {ccol}: {mismatch_counts[ecol]}건")
    for ex in mismatch_examples[ecol]:
        print(f"    예: key={ex[0]} 엑셀='{ex[1]}' 수집='{ex[2]}'")

# status 컬럼(csv) 분포 확인 - stale_warning 등 비정상 항목
print()
print("[수집 CSV status 분포]")
print(csv["status"].value_counts())
