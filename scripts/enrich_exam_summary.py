# -*- coding: utf-8 -*-
"""step9_exam_summary.csv에 마스터 엑셀의 지역/학년/학기/연도/중간-기말 정보를 병합."""
import sys
sys.stdout.reconfigure(encoding="utf-8")
import pandas as pd

xls = pd.ExcelFile(r"D:\ddddashboard\data\텍스트 검수 리스트.xlsx")
meta_rows = []
for s in ["2. 고등내신(시험지)", "4. 중등내신(시험지)"]:
    df = pd.read_excel(xls, sheet_name=s)
    col = "시험지명(문제편집기 조회용)"
    df = df.dropna(subset=[col])
    df = df.drop_duplicates(subset=[col])
    keep = df[[col, "학년", "학기", "연도", "중간/기말", "지역(시/도)", "지역(구)"]].copy()
    keep.columns = ["textbook_name", "학년", "학기", "연도", "중간기말", "지역시도", "지역구"]
    keep["연도"] = pd.to_numeric(keep["연도"], errors="coerce").astype("Int64").astype(str).replace("<NA>", "")
    meta_rows.append(keep)
meta = pd.concat(meta_rows, ignore_index=True)
meta = meta.drop_duplicates(subset=["textbook_name"])

exams = pd.read_csv(r"D:\ddddashboard\data\step9_exam_summary.csv", dtype=str)
before = len(exams)
exams = exams.merge(meta, on="textbook_name", how="left")
print(f"병합 전 {before}행, 병합 후 {len(exams)}행")
print("지역 정보 결측:", exams["지역시도"].isna().sum())

exams.to_csv(r"D:\ddddashboard\data\step9_exam_summary.csv", index=False, encoding="utf-8-sig")
print("저장 완료")
