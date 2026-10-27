# STEP 1: 목록.xlsx 파일 구조 확인 (읽기 전용, 원본 파일을 수정하지 않음)
import pandas as pd
from pathlib import Path

SRC = Path(__file__).parent / "목록.xlsx"

print(f"[파일 경로] {SRC}")
print(f"[파일 존재 여부] {SRC.exists()}")
print(f"[파일 크기] {SRC.stat().st_size:,} bytes")
print()

# 1. 시트 목록 확인
xls = pd.ExcelFile(SRC, engine="openpyxl")
print(f"[시트 목록] {xls.sheet_names}")
print()

# 2. 각 시트별로 기본 정보 출력
for sheet_name in xls.sheet_names:
    df = pd.read_excel(SRC, sheet_name=sheet_name, engine="openpyxl")
    print("=" * 60)
    print(f"[시트명] {sheet_name}")
    print(f"[행 수] {len(df)}")
    print(f"[열 수] {len(df.columns)}")
    print(f"[컬럼명 목록]")
    for i, col in enumerate(df.columns):
        print(f"  {i}: {repr(col)}")
    print()
    print("[상위 5행 미리보기]")
    print(df.head(5).to_string())
    print()
    print("[컬럼별 데이터 타입]")
    print(df.dtypes)
    print()
    print("[컬럼별 결측치 개수]")
    print(df.isnull().sum())
    print()
    print(f"[완전 중복 행 개수] {df.duplicated().sum()}")
    print()
