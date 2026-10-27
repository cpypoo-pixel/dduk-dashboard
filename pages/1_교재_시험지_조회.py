# -*- coding: utf-8 -*-
"""교재·시험지 통합 조회 (화면 2+3 통합)
교재와 내신 시험지를 한 화면에서 같이 검색·필터링한다 (예: 고등만 보기 = 교재+내신 둘 다 포함).
자료를 선택하면 문항별 상세를 확인한다. 읽기 전용.
"""
import pandas as pd
import plotly.express as px
import streamlit as st
from dashboard_style import inject as inject_style, apply_korean_font
from dashboard_auth import require_login

st.set_page_config(page_title="교재·시험지 조회", layout="wide", page_icon="🔍")
require_login()
inject_style()

UNIFIED_PATH = "data/unified_summary.csv"
BOOK_ITEMS_PATH = "data/step8_all_items.csv"
EXAM_ITEMS_PATH = "data/step9_all_items.csv"


@st.cache_data(ttl="6h")
def load_unified():
    df = pd.read_csv(UNIFIED_PATH, dtype=str, keep_default_na=False)
    for c in ["api_item_count", "review_done_count", "review_pending_count", "twin_total", "similar_total"]:
        df[c] = pd.to_numeric(df[c], errors="coerce").fillna(0).astype(int)
    df["review_rate"] = (df["review_done_count"] / df["api_item_count"].replace(0, pd.NA) * 100).round(1)
    return df


@st.cache_data(ttl="6h")
def load_items(data_type, book_id):
    path = BOOK_ITEMS_PATH if data_type == "교재" else EXAM_ITEMS_PATH
    df = pd.read_csv(path, dtype=str)
    df = df[df["book_id"] == book_id].copy()
    for c in ["twin_count", "similar_count", "other_relation_count"]:
        df[c] = pd.to_numeric(df[c], errors="coerce").fillna(0).astype(int)
    return df


with st.spinner("데이터 불러오는 중..."):
    data = load_unified()

st.title("🔍 교재·시험지 조회")
st.caption(f"교재 {len(data[data['data_type']=='교재']):,}권 + 내신 시험지 {len(data[data['data_type']=='내신']):,}건 · 통합 조회")
st.caption(f"🕒 데이터 기준 시각: {data['collected_at'].max()}")

# ---------- 필터 ----------
st.subheader("🔍 검색 / 필터")
f1, f2, f3, f4 = st.columns(4)
with f1:
    type_options = ["전체", "교재", "내신"]
    sel_type = st.selectbox("자료 유형", type_options)
with f2:
    level_options = ["전체", "초등", "중등", "고등"]
    sel_level = st.selectbox("학교급", level_options)
with f3:
    sido_options = ["전체"] + sorted([x for x in data["지역시도"].dropna().unique().tolist() if x])
    sel_sido = st.selectbox("지역(시/도, 내신만 해당)", sido_options)
with f4:
    year_options = ["전체"] + sorted([x for x in data["연도"].dropna().unique().tolist() if x], reverse=True)
    sel_year = st.selectbox("연도(내신만 해당)", year_options)

f5, f6, f7 = st.columns(3)
with f5:
    name_q = st.text_input("교재명/시험지명 검색 (학교명 포함)", placeholder="예: 강릉여고, 최상위수학")
with f6:
    review_options = ["전체", "검수 100% 완료", "미완료 문항 있음"]
    sel_review = st.selectbox("검수 상태", review_options)
with f7:
    twin_options = ["전체", "쌍둥이 생성됨", "쌍둥이 없음"]
    sel_twin = st.selectbox("쌍둥이 생성 여부", twin_options)

filtered = data.copy()
if sel_type != "전체":
    filtered = filtered[filtered["data_type"] == sel_type]
if sel_level != "전체":
    filtered = filtered[filtered["school_level"] == sel_level]
if sel_sido != "전체":
    filtered = filtered[filtered["지역시도"] == sel_sido]
if sel_year != "전체":
    filtered = filtered[filtered["연도"] == sel_year]
if name_q:
    filtered = filtered[filtered["textbook_name"].str.contains(name_q, na=False)]
if sel_review == "검수 100% 완료":
    filtered = filtered[filtered["review_pending_count"] == 0]
elif sel_review == "미완료 문항 있음":
    filtered = filtered[filtered["review_pending_count"] > 0]
if sel_twin == "쌍둥이 생성됨":
    filtered = filtered[filtered["twin_total"] > 0]
elif sel_twin == "쌍둥이 없음":
    filtered = filtered[filtered["twin_total"] == 0]

sort_col = st.selectbox("정렬 기준", ["문항수 많은 순", "검수완료율 낮은 순", "쌍둥이 많은 순", "이름순"])
if sort_col == "문항수 많은 순":
    filtered = filtered.sort_values("api_item_count", ascending=False)
elif sort_col == "검수완료율 낮은 순":
    filtered = filtered.sort_values("review_rate", ascending=True)
elif sort_col == "쌍둥이 많은 순":
    filtered = filtered.sort_values("twin_total", ascending=False)
else:
    filtered = filtered.sort_values("textbook_name")

# ---------- 필터 결과 요약 칩 ----------
k1, k2, k3, k4 = st.columns(4)
k1.metric("조건에 맞는 자료", f"{len(filtered):,}건")
k2.metric("문항 합계", f"{filtered['api_item_count'].sum():,}")
avg_rate = filtered["review_rate"].mean() if len(filtered) else 0
k3.metric("평균 검수완료율", f"{avg_rate:.1f}%")
k4.metric("쌍둥이 합계", f"{filtered['twin_total'].sum():,}")

st.dataframe(
    filtered[[
        "textbook_name", "data_type", "school_level", "sheet", "지역시도", "연도",
        "api_item_count", "review_done_count", "review_pending_count",
        "review_rate", "twin_total",
    ]].rename(columns={
        "textbook_name": "이름", "data_type": "유형", "school_level": "학교급", "sheet": "분류",
        "지역시도": "시/도", "api_item_count": "문항수", "review_done_count": "검수완료",
        "review_pending_count": "검수미완료", "review_rate": "검수완료율", "twin_total": "쌍둥이",
    }),
    use_container_width=True, hide_index=True, height=420,
    column_config={
        "검수완료율": st.column_config.ProgressColumn("검수완료율", format="%.1f%%", min_value=0, max_value=100),
        "문항수": st.column_config.NumberColumn("문항수", format="%d"),
        "검수완료": st.column_config.NumberColumn("검수완료", format="%d"),
        "검수미완료": st.column_config.NumberColumn("검수미완료", format="%d"),
        "쌍둥이": st.column_config.NumberColumn("쌍둥이", format="%d"),
    },
)

st.download_button(
    "⬇ 현재 필터 결과 CSV 다운로드",
    data=filtered.to_csv(index=False).encode("utf-8-sig"),
    file_name="교재시험지_필터결과.csv",
    mime="text/csv",
)

st.divider()

# ---------- 지역/연도별 보유 현황 (내신이 포함된 경우만) ----------
exam_part = filtered[filtered["data_type"] == "내신"]
if len(exam_part) > 0:
    st.subheader("🗺️ 내신 시험지 — 지역·연도별 보유 현황")
    col_a, col_b = st.columns(2)
    with col_a:
        region_dist = exam_part.groupby("지역시도").size().reset_index(name="건수").sort_values("건수", ascending=False)
        fig_a = px.bar(region_dist, x="지역시도", y="건수", color="건수", color_continuous_scale="Tealgrn")
        fig_a.update_layout(height=300, margin=dict(t=20, b=10), coloraxis_showscale=False, title="시/도별 건수")
        apply_korean_font(fig_a)
        st.plotly_chart(fig_a, use_container_width=True, theme=None, config={"displayModeBar": False})
    with col_b:
        year_dist = exam_part.groupby("연도").size().reset_index(name="건수")
        year_dist = year_dist[year_dist["연도"] != ""].sort_values("연도")
        fig_b = px.area(year_dist, x="연도", y="건수", markers=True)
        fig_b.update_traces(line_color="#6366f1", fillcolor="rgba(99,102,241,0.18)")
        fig_b.update_layout(height=300, margin=dict(t=20, b=10), title="연도별 건수")
        apply_korean_font(fig_b)
        st.plotly_chart(fig_b, use_container_width=True, theme=None, config={"displayModeBar": False})
    st.divider()

# ---------- 상세: 문항별 목록 ----------
st.subheader("📄 문항 상세")
if len(filtered) == 0:
    st.info("조건에 맞는 자료가 없습니다.")
else:
    pick_name = st.selectbox("자료 선택", filtered["textbook_name"].tolist())
    pick_row = filtered[filtered["textbook_name"] == pick_name].iloc[0]
    book_id = pick_row["book_id"]
    data_type = pick_row["data_type"]

    m1, m2, m3, m4, m5 = st.columns(5)
    m1.metric("유형", data_type)
    m2.metric("문항수", f"{pick_row['api_item_count']:,}")
    m3.metric("검수완료", f"{pick_row['review_done_count']:,}")
    m4.metric("쌍둥이", f"{pick_row['twin_total']:,}")
    m5.metric("유사", f"{pick_row['similar_total']:,}")

    with st.spinner("문항 상세 불러오는 중..."):
        book_items = load_items(data_type, book_id)
        book_items["page_num"] = pd.to_numeric(book_items["page"], errors="coerce")
        book_items["item_num_sort"] = pd.to_numeric(book_items["item_num"], errors="coerce")
        book_items = book_items.sort_values(["page_num", "item_num_sort"])
        book_items["is_review_status"] = book_items["is_review_status"].fillna("미확인").replace("", "미확인")

    col_chart, col_space = st.columns([1, 3])
    with col_chart:
        status_df = book_items["is_review_status"].value_counts().reset_index()
        status_df.columns = ["상태", "문항수"]
        fig_c = px.pie(status_df, names="상태", values="문항수", hole=0.55,
                       color_discrete_sequence=px.colors.qualitative.Set2)
        fig_c.update_layout(height=220, margin=dict(l=0, r=0, t=10, b=0), showlegend=True,
                           legend=dict(orientation="h", y=-0.15))
        apply_korean_font(fig_c)
        st.plotly_chart(fig_c, use_container_width=True, theme=None, config={"displayModeBar": False})

    display_cols = [
        "page", "item_num", "item_id", "item_kind_nm", "difficulty_nm",
        "is_review_status", "is_text_conversion_status", "del_yn",
        "twin_count", "similar_count",
    ]
    rename_map = {
        "page": "페이지", "item_num": "문제번호", "item_id": "문제코드",
        "item_kind_nm": "문제종류", "difficulty_nm": "난이도",
        "is_review_status": "문항검수", "is_text_conversion_status": "텍스트변환",
        "del_yn": "삭제여부", "twin_count": "쌍둥이", "similar_count": "유사",
    }
    if data_type == "교재":
        display_cols = display_cols[:5] + ["upper1_taxo_nm", "upper2_taxo_nm", "upper3_taxo_nm", "taxo_nm"] + display_cols[5:]
        rename_map.update({"upper1_taxo_nm": "소단원", "upper2_taxo_nm": "중단원", "upper3_taxo_nm": "대단원", "taxo_nm": "세부단원"})

    st.dataframe(
        book_items[display_cols].rename(columns=rename_map),
        use_container_width=True, hide_index=True, height=420,
    )

    st.download_button(
        f"⬇ {pick_name} 문항 전체 CSV 다운로드",
        data=book_items.to_csv(index=False).encode("utf-8-sig"),
        file_name=f"{pick_name}_문항목록.csv",
        mime="text/csv",
    )
