# STEP 2: 목록.xlsx -> textbook_items.csv (표준화된 원본 문항 목록)
# - 원본 엑셀 파일은 읽기만 하며 수정하지 않는다.
# - 엑셀에 없는 값(문제코드 등)은 임의로 만들지 않고 "미확인"으로 둔다.
import pandas as pd
from pathlib import Path
from datetime import datetime

BASE_DIR = Path(__file__).parent.parent
SRC = BASE_DIR / "목록.xlsx"
OUT = BASE_DIR / "data" / "textbook_items.csv"

# 교재 식별값: 엑셀 자체에는 교재 식별 정보가 없어, 관리자 페이지 화면/URL에서
# 수동으로 확인한 값을 고정 상수로 사용한다 (사용자 확인 완료, 2026-10-22).
# 출처: adm.mswitch.co.kr/.../book-item-edit?book_type=02&group_code=SNB0000200&center_seq=664
# 화면 표시명: "고1 2학기 2022개정 수학 셀B 공통수학2"
TEXTBOOK_ID = "SNB0000200_664"
TEXTBOOK_NAME = "고1 2학기 2022개정 수학 셀B 공통수학2"

COLLECTED_AT = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

df = pd.read_excel(SRC, sheet_name="Sheet1", engine="openpyxl")

# 실제 컬럼명 기준 매핑 (STEP 1에서 확인한 컬럼명 그대로 사용)
out = pd.DataFrame({
    "textbook_id": TEXTBOOK_ID,
    "textbook_name": TEXTBOOK_NAME,
    "list_no": df["No. "].astype(str).str.strip(),
    "page": df["페이지"],
    "question_number": df["문제번호"],
    "question_code": "미확인",  # 목록 엑셀에는 문제코드 컬럼이 없음. 상세화면에서만 확인 가능.
    "question_type": df["문제종류"],
    "difficulty": df["난이도"],
    "major_unit": df["대단원"],
    "middle_unit": df["중단원"],
    "minor_unit": df["소단원"],
    "unit_name": df["단원명"],
    "item_review_status": df["문항검수"],
    "text_conversion_status": df["텍스트변환"],
    "deleted": df["문제삭제"],
    "review_completed_at": df["검수완료일시"],
    "review_cancelled_at": df["검수취소일시"],
    "source_file": "목록.xlsx",
    "collected_at": COLLECTED_AT,
})

# (page, question_number) 조합이 유일 키인지 재확인
dup_count = out.duplicated(subset=["page", "question_number"]).sum()
assert dup_count == 0, f"(page, question_number) 중복 {dup_count}건 발견 - 처리 중단"

OUT.parent.mkdir(parents=True, exist_ok=True)
out.to_csv(OUT, index=False, encoding="utf-8-sig")

print(f"[저장 완료] {OUT}")
print(f"[행 수] {len(out)}")
print(f"[컬럼] {list(out.columns)}")
print()
print("[요약 보고서]")
print(f"- 전체 원본 문항 수: {len(out)}")
print(f"- 문항검수 상태별: {out['item_review_status'].value_counts().to_dict()}")
print(f"- 텍스트변환 상태별: {out['text_conversion_status'].value_counts().to_dict()}")
print(f"- 삭제 여부별: {out['deleted'].value_counts().to_dict()}")
print(f"- 대단원별 문항 수: {out['major_unit'].value_counts().to_dict()}")
print(f"- 결측치 (컬럼별):")
print(out.isnull().sum())
