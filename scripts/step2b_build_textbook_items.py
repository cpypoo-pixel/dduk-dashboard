# -*- coding: utf-8 -*-
"""STEP 2 (재실행): 올바른 교재(중1 1학기 2022개정 수학 최상위수학 라이트)의
관리페이지 원본 엑셀(목록_최상위수학라이트.xlsx)로 textbook_items.csv를 다시 만든다.
(기존 textbook_items.csv는 잘못된 교재(셀B)용이었음)"""
import sys
import pandas as pd

sys.stdout.reconfigure(encoding="utf-8")

SRC = r"D:\ddddashboard\data\목록_최상위수학라이트.xlsx"
OUT = r"D:\ddddashboard\data\textbook_items.csv"
TEXTBOOK_ID = "odapnote_최상위수학라이트_중1_1학기_2022개정"
TEXTBOOK_NAME = "중1 1학기 2022개정 수학 최상위수학 라이트"

df = pd.read_excel(SRC)

out = pd.DataFrame(index=df.index)
out["page"] = df["페이지"].astype(int).astype(str).str.zfill(4)
out["question_number"] = df["문제번호"].astype(int).astype(str).str.zfill(4)
out["item_review_status"] = df["문항검수"]
out["text_conversion_status"] = df["텍스트변환"]
out["question_type"] = df["문제종류"]
out["difficulty"] = df["난이도"]
out["large_unit"] = df["대단원"]
out["medium_unit"] = df["중단원"]
out["small_unit"] = df["소단원"]
out["unit_name"] = df["단원명"]
out["deleted"] = df["문제삭제"]
out["review_completed_at"] = df["검수완료일시"]
out["review_cancelled_at"] = df["검수취소일시"]
out["source"] = "excel_export"
out.insert(0, "textbook_name", TEXTBOOK_NAME)
out.insert(0, "textbook_id", TEXTBOOK_ID)

out.to_csv(OUT, index=False, encoding="utf-8-sig")
print(f"[완료] {OUT} ({len(out)}행)")
print(out.head(3).to_string())
