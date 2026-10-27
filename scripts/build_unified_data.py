# -*- coding: utf-8 -*-
"""교재 DB(step8)와 내신 시험지 DB(step9)를 하나의 통합 데이터셋으로 합친다.
학교급(초/중/고)을 공통 필드로 추출해서 교재+내신을 한 화면에서 같이 필터링할 수 있게 한다."""
import sys, re
sys.stdout.reconfigure(encoding="utf-8")
import pandas as pd

BOOKS_SUMMARY = "D:/ddddashboard/data/step8_book_summary.csv"
EXAMS_SUMMARY = "D:/ddddashboard/data/step9_exam_summary.csv"
BOOKS_ITEMS = "D:/ddddashboard/data/step8_all_items.csv"
EXAMS_ITEMS = "D:/ddddashboard/data/step9_all_items.csv"

LEVEL_MAP = {"초": "초등", "중": "중등", "고": "고등"}


def extract_level_grade(name):
    m = re.match(r"^(초|중|고)(\d)", str(name))
    if m:
        return LEVEL_MAP[m.group(1)], f"{m.group(1)}{m.group(2)}"
    return "미확인", ""


# ---------- summary ----------
books = pd.read_csv(BOOKS_SUMMARY, dtype=str)
exams = pd.read_csv(EXAMS_SUMMARY, dtype=str)

books["data_type"] = "교재"
exams["data_type"] = "내신"

lv = books["textbook_name"].apply(extract_level_grade)
books["school_level"] = [x[0] for x in lv]
books["grade"] = [x[1] for x in lv]
books["지역시도"] = ""
books["지역구"] = ""
books["연도"] = ""
books["중간기말"] = ""

# 내신은 학년 컬럼을 그대로 사용 (고1~고3, 중1~중3)
exams["school_level"] = exams["학년"].str[0].map(LEVEL_MAP).fillna("미확인")
exams["grade"] = exams["학년"]

common_cols = [
    "book_id", "textbook_name", "data_type", "sheet", "school_level", "grade",
    "지역시도", "지역구", "연도", "중간기말",
    "api_item_count", "review_done_count", "review_pending_count", "deleted_count",
    "twin_total", "similar_total", "collected_at",
]
unified_summary = pd.concat([books[common_cols], exams[common_cols]], ignore_index=True)
unified_summary["api_item_count"] = pd.to_numeric(unified_summary["api_item_count"], errors="coerce").fillna(0).astype(int)
unified_summary["review_done_count"] = pd.to_numeric(unified_summary["review_done_count"], errors="coerce").fillna(0).astype(int)
unified_summary["review_pending_count"] = pd.to_numeric(unified_summary["review_pending_count"], errors="coerce").fillna(0).astype(int)
unified_summary["twin_total"] = pd.to_numeric(unified_summary["twin_total"], errors="coerce").fillna(0).astype(int)
unified_summary["similar_total"] = pd.to_numeric(unified_summary["similar_total"], errors="coerce").fillna(0).astype(int)
unified_summary["review_rate"] = (
    unified_summary["review_done_count"] / unified_summary["api_item_count"].replace(0, pd.NA) * 100
).round(1)

unified_summary.to_csv("D:/ddddashboard/data/unified_summary.csv", index=False, encoding="utf-8-sig")
print(f"[요약 통합 완료] {len(unified_summary)}행 -> data/unified_summary.csv")
print(unified_summary["school_level"].value_counts())
print(unified_summary["data_type"].value_counts())

# ---------- items (book_id -> data_type 매핑만 추가해서 합침, 필요시 지연 로드) ----------
book_ids_books = set(books["book_id"])
book_ids_exams = set(exams["book_id"])
print(f"\n[items] 교재 book_id {len(book_ids_books)}개, 내신 book_id {len(book_ids_exams)}개")
print("[완료] items 파일은 book_id로 구분 가능하므로 그대로 두고 조회 시 병합")
