# -*- coding: utf-8 -*-
"""전일 스냅샷(unified_summary_prev.csv)과 오늘 결과(unified_summary.csv)를 비교해
data/diff_report.csv(신규/삭제/변경 자료 목록)를 생성한다."""
import pandas as pd
from pathlib import Path

BASE_DIR = Path(__file__).parent.parent
DATA_DIR = BASE_DIR / "data"

METRICS = ["api_item_count", "review_done_count", "review_pending_count",
           "deleted_count", "twin_total", "similar_total"]


HISTORY_DIR = DATA_DIR / "diff_history"


def history_filename(new_at):
    return "diff_" + new_at.replace(" ", "_").replace(":", "")[:15] + ".csv"


def write_history(diff_df, prev_at, new_at):
    HISTORY_DIR.mkdir(exist_ok=True)
    out = diff_df.copy()
    out.insert(0, "비교기준일시", prev_at)
    out.insert(0, "갱신일시", new_at)
    out.to_csv(HISTORY_DIR / history_filename(new_at), index=False, encoding="utf-8-sig")


def main():
    prev_path = DATA_DIR / "unified_summary_prev.csv"
    new_path = DATA_DIR / "unified_summary.csv"
    if not prev_path.exists():
        print("[diff] 이전 스냅샷이 없어 비교를 건너뜁니다 (최초 실행)")
        return

    cols = ["book_id", "textbook_name", "data_type"] + METRICS
    prev_full = pd.read_csv(prev_path)
    new_full = pd.read_csv(new_path)
    prev_at = str(prev_full["collected_at"].max())
    new_at = str(new_full["collected_at"].max())
    prev = prev_full[cols]
    new = new_full[cols]

    merged = prev.merge(new, on="book_id", how="outer", suffixes=("_전일", "_오늘"), indicator=True)
    merged["textbook_name"] = merged["textbook_name_오늘"].fillna(merged["textbook_name_전일"])
    merged["data_type"] = merged["data_type_오늘"].fillna(merged["data_type_전일"])
    merged["상태"] = merged["_merge"].map({"left_only": "삭제됨", "right_only": "신규", "both": "기존"}).astype(str)

    for m in METRICS:
        merged[f"{m}_전일"] = merged[f"{m}_전일"].fillna(0).astype(int)
        merged[f"{m}_오늘"] = merged[f"{m}_오늘"].fillna(0).astype(int)
        merged[f"{m}_변화"] = merged[f"{m}_오늘"] - merged[f"{m}_전일"]

    changed_mask = merged["상태"] != "기존"
    for m in METRICS:
        changed_mask = changed_mask | (merged[f"{m}_변화"] != 0)

    out_cols = ["book_id", "textbook_name", "data_type", "상태"]
    for m in METRICS:
        out_cols += [f"{m}_전일", f"{m}_오늘", f"{m}_변화"]
    diff_df = merged.loc[changed_mask, out_cols].copy()
    diff_df.loc[diff_df["상태"] == "기존", "상태"] = "변경"
    diff_df.to_csv(DATA_DIR / "diff_report.csv", index=False, encoding="utf-8-sig")

    # 갱신일별 조회용 이력: 갱신 시각마다 파일을 하나씩 남긴다 (하루 평균 수십 KB).
    # 며칠 건너뛰고 갱신하면 그 사이 변화가 한 파일에 합쳐지므로 비교기준일시를 함께 기록한다.
    if prev_at != new_at:
        write_history(diff_df, prev_at, new_at)

    new_count = (diff_df["상태"] == "신규").sum()
    removed_count = (diff_df["상태"] == "삭제됨").sum()
    changed_count = (diff_df["상태"] == "변경").sum()
    print(f"[diff] 변경된 자료 {len(diff_df)}건 (신규 {new_count} / 삭제 {removed_count} / 변경 {changed_count})")
    for m in METRICS:
        total_delta = int(diff_df[f"{m}_변화"].sum()) if len(diff_df) else 0
        if total_delta != 0:
            print(f"[diff]   {m} 총 변화: {total_delta:+d}")


if __name__ == "__main__":
    main()
