# -*- coding: utf-8 -*-
"""수집 원본(step8/step9_all_items.csv)에서 자료마다 값이 같은 열(textbook_name, sheet, collected_at)을 빼
GitHub 배포용 data/items_book.csv, data/items_exam.csv 를 만든다.
- 빠진 열은 unified_summary.csv 에 자료당 1번씩 있어서, 화면에서 book_id 로 다시 붙인다 (정보 손실 없음).
- collected_at 이 문항 줄마다 달라지던 것이 사라져서, 갱신 때 바뀐 줄만 git 에 변경분으로 잡힌다."""
import pandas as pd
from pathlib import Path

DATA_DIR = Path(__file__).parent.parent / "data"
DROP_COLS = ["textbook_name", "sheet", "collected_at"]

TARGETS = {
    "step8_all_items.csv": "items_book.csv",
    "step9_all_items.csv": "items_exam.csv",
}


def main():
    unified = pd.read_csv(DATA_DIR / "unified_summary.csv", dtype=str, keep_default_na=False)
    um = unified.set_index("book_id")[DROP_COLS]
    for src, dst in TARGETS.items():
        df = pd.read_csv(DATA_DIR / src, dtype=str, keep_default_na=False)
        # 빼도 되는 열이 정말 자료 단위로 같은지 확인한다 (다르면 정보가 사라지므로 중단).
        per_book = df[["book_id"] + DROP_COLS].drop_duplicates()
        joined = per_book.merge(um, left_on="book_id", right_index=True, how="left", suffixes=("", "_u"))
        for c in DROP_COLS:
            bad = int((joined[c] != joined[c + "_u"]).sum())
            if bad:
                raise SystemExit(f"[중단] {src}: {c} 가 unified_summary 와 다른 자료가 {bad}건 있어 슬림 파일을 만들지 않습니다.")
        df.drop(columns=DROP_COLS).to_csv(DATA_DIR / dst, index=False, encoding="utf-8")
        size_mb = (DATA_DIR / dst).stat().st_size / 1e6
        print(f"[슬림] {dst}: {len(df):,}줄, {size_mb:.1f}MB (원본 {(DATA_DIR / src).stat().st_size / 1e6:.1f}MB)")


if __name__ == "__main__":
    main()
