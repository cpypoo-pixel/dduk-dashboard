# -*- coding: utf-8 -*-
"""오답노트 DB 대시보드 (STEP 7)
data/final_items.csv (STEP 6에서 검증 완료된 데이터)를 읽어 보여준다. 읽기 전용.
"""
import pandas as pd
import streamlit as st
from dashboard_auth import require_login

st.set_page_config(page_title="오답노트 DB 대시보드", layout="wide")
require_login()

DATA_PATH = "data/final_items.csv"


@st.cache_data
def load_data():
    df = pd.read_csv(DATA_PATH, dtype=str)
    df["twin_count"] = pd.to_numeric(df["twin_count"], errors="coerce").fillna(0).astype(int)
    df["similar_count"] = pd.to_numeric(df["similar_count"], errors="coerce").fillna(0).astype(int)
    df["tabs_count"] = pd.to_numeric(df["tabs_count"], errors="coerce").fillna(0).astype(int)
    df["page_num"] = pd.to_numeric(df["page"], errors="coerce")
    df["qno_num"] = pd.to_numeric(df["question_number"], errors="coerce")
    return df


df = load_data()

st.title("오답노트 DB 대시보드")
st.caption(f"교재: {df['textbook_name'].iloc[0]} · 총 {len(df)}문항")

# ---------- 요약 카드 ----------
c1, c2, c3, c4, c5 = st.columns(5)
c1.metric("전체 문항 수", f"{len(df)}")
c2.metric("검수완료", f"{(df['item_review_status'] == '완료').sum()}")
c3.metric("검수 작업중", f"{(df['item_review_status'] == '작업중').sum()}")
c4.metric("쌍둥이 문항 총합", f"{df['twin_count'].sum()}")
c5.metric("미확인 데이터", f"{(df['data_status'] == '미확인').sum()}")

st.divider()

# ---------- 필터 ----------
st.subheader("검색 / 필터")
f1, f2, f3, f4 = st.columns(4)
with f1:
    unit_options = ["전체"] + sorted(df["large_unit"].dropna().unique().tolist())
    sel_unit = st.selectbox("대단원", unit_options)
with f2:
    status_options = ["전체"] + sorted(df["item_review_status"].dropna().unique().tolist())
    sel_status = st.selectbox("검수 상태", status_options)
with f3:
    diff_options = ["전체"] + sorted(df["difficulty"].dropna().unique().tolist())
    sel_diff = st.selectbox("난이도", diff_options)
with f4:
    min_twin = st.number_input("쌍둥이 최소 개수", min_value=0, max_value=int(df["twin_count"].max()), value=0)

q = st.text_input("문제코드 / 페이지 / 문제번호 검색")

filtered = df.copy()
if sel_unit != "전체":
    filtered = filtered[filtered["large_unit"] == sel_unit]
if sel_status != "전체":
    filtered = filtered[filtered["item_review_status"] == sel_status]
if sel_diff != "전체":
    filtered = filtered[filtered["difficulty"] == sel_diff]
filtered = filtered[filtered["twin_count"] >= min_twin]
if q:
    filtered = filtered[
        filtered["question_code"].str.contains(q, na=False)
        | filtered["page"].str.contains(q, na=False)
        | filtered["question_number"].str.contains(q, na=False)
    ]

st.caption(f"조건에 맞는 문항: {len(filtered)}건")

st.divider()

# ---------- 단원별 집계 ----------
st.subheader("대단원별 집계")
unit_summary = (
    df.groupby("large_unit", dropna=False)
    .agg(
        문항수=("question_code", "count"),
        검수완료=("item_review_status", lambda s: (s == "완료").sum()),
        쌍둥이합계=("twin_count", "sum"),
        유사합계=("similar_count", "sum"),
    )
    .reset_index()
    .rename(columns={"large_unit": "대단원"})
)
st.dataframe(unit_summary, use_container_width=True, hide_index=True)

st.divider()

# ---------- 쌍둥이/유사 문항 집계 ----------
st.subheader("쌍둥이 / 유사 문항 생성 현황")
col_a, col_b = st.columns(2)
with col_a:
    st.caption("문항당 쌍둥이 개수 분포")
    twin_dist = df["twin_count"].value_counts().sort_index()
    st.bar_chart(twin_dist)
with col_b:
    st.caption("문항당 유사문항 개수 분포")
    similar_dist = df["similar_count"].value_counts().sort_index()
    if similar_dist.sum() == 0:
        st.info("이 교재에는 유사문항이 생성된 항목이 없습니다.")
    else:
        st.bar_chart(similar_dist)

st.divider()

# ---------- 문항별 상세 테이블 ----------
st.subheader("문항별 상세 목록")
display_cols = [
    "page", "question_number", "question_code", "item_review_status",
    "text_conversion_status", "question_type", "difficulty",
    "large_unit", "medium_unit", "small_unit", "unit_name",
    "twin_count", "similar_count", "deleted", "data_status",
]
filtered_sorted = filtered.sort_values(["page_num", "qno_num"])
st.dataframe(
    filtered_sorted[display_cols],
    use_container_width=True,
    hide_index=True,
    height=420,
)

# ---------- 문항 상세 보기 ----------
st.subheader("문항 상세 보기")
if len(filtered) > 0:
    pick = st.selectbox(
        "문항 선택 (페이지_문제번호)",
        (filtered["page"] + "_" + filtered["question_number"]).tolist(),
    )
    row = filtered[(filtered["page"] + "_" + filtered["question_number"]) == pick].iloc[0]
    d1, d2 = st.columns(2)
    with d1:
        st.write("**기본 정보**")
        st.json({
            "문제코드": row["question_code"],
            "페이지": row["page"],
            "문제번호": row["question_number"],
            "문제종류": row["question_type"],
            "난이도": row["difficulty"],
            "문항검수": row["item_review_status"],
            "텍스트변환": row["text_conversion_status"],
            "문제삭제": row["deleted"],
        })
        st.write("**단원 정보**")
        st.json({
            "대단원": row["large_unit"],
            "중단원": row["medium_unit"],
            "소단원": row["small_unit"],
            "단원명": row["unit_name"],
        })
    with d2:
        st.write("**등록/수정 정보**")
        st.json({
            "등록자": row["registered_by"],
            "등록일시": row["registered_at"],
            "수정자": row["modified_by"],
            "수정일시": row["modified_at"],
            "검수완료일시": row["review_completed_at"],
            "검수취소일시": row["review_cancelled_at"],
        })
        st.write(f"**쌍둥이 문항**: {row['twin_count']}개  /  **유사 문항**: {row['similar_count']}개")
        st.caption(f"탭 목록: {row['tabs_present']}")
else:
    st.info("조건에 맞는 문항이 없습니다.")

st.divider()

# ---------- CSV 다운로드 ----------
st.subheader("데이터 다운로드")
st.download_button(
    "필터링된 데이터 CSV 다운로드",
    data=filtered.to_csv(index=False).encode("utf-8-sig"),
    file_name="오답노트_필터결과.csv",
    mime="text/csv",
)
st.download_button(
    "전체 데이터 CSV 다운로드",
    data=df.to_csv(index=False).encode("utf-8-sig"),
    file_name="오답노트_전체데이터.csv",
    mime="text/csv",
)
