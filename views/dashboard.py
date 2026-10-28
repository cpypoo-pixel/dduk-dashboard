# -*- coding: utf-8 -*-
"""DB 통합 대시보드 (화면 1)
22개정 교재 + 내신 시험지 전체의 데이터 확보/구축/검수 현황을 한눈에 보여준다. 읽기 전용.
"""
from pathlib import Path
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import streamlit as st
from dashboard_style import inject as inject_style, apply_korean_font
from dashboard_auth import require_login

require_login()
inject_style()

UNIFIED_PATH = "data/unified_summary.csv"


@st.cache_data(ttl="6h")
def load_unified():
    df = pd.read_csv(UNIFIED_PATH, dtype=str, keep_default_na=False)
    for c in ["api_item_count", "review_done_count", "review_pending_count", "twin_total", "similar_total"]:
        df[c] = pd.to_numeric(df[c], errors="coerce").fillna(0).astype(int)
    df["review_rate"] = (df["review_done_count"] / df["api_item_count"].replace(0, pd.NA) * 100).round(1)
    return df


with st.spinner("데이터 불러오는 중..."):
    data = load_unified()

books = data[data["data_type"] == "교재"]
exams = data[data["data_type"] == "내신"]

st.title("📊 DB 통합 대시보드", anchor=False)
st.caption("2022개정 교재 + 내신 시험지(고등·중등) 전체 데이터 확보 · 문제 생성 · 검수 현황")
last_updated = data["collected_at"].max()
st.caption(f"🕒 데이터 기준 시각: {last_updated} (수동 갱신 · 아래 '교재·시험지 조회' 페이지에서 상세 확인)")

# ---------- 전체 핵심 요약 ----------
total_sources = len(data)
total_items_all = data["api_item_count"].sum()
total_twin_all = data["twin_total"].sum()
total_done_all = data["review_done_count"].sum()
total_pending_all = data["review_pending_count"].sum()
overall_rate = total_done_all / total_items_all * 100

c1, c2, c3, c4 = st.columns(4)
c1.metric("등록 자료 수 (교재+시험지)", f"{total_sources:,}건")
c2.metric("원본 문제 수", f"{total_items_all:,}")
c3.metric("쌍둥이 문제 수", f"{total_twin_all:,}")
c4.metric("검수 완료율", f"{overall_rate:.1f}%")

# ---------- 전체 검수 진행률 게이지 ----------
gcol1, gcol2 = st.columns([1, 2])
with gcol1:
    gauge = go.Figure(go.Indicator(
        mode="gauge+number",
        value=overall_rate,
        number={"suffix": "%", "font": {"size": 34}},
        title={"text": "전체 검수 진행률", "font": {"size": 15}},
        gauge={
            "axis": {"range": [0, 100]},
            "bar": {"color": "#6366f1"},
            "bgcolor": "rgba(0,0,0,0)",
            "steps": [
                {"range": [0, 40], "color": "rgba(239,68,68,0.18)"},
                {"range": [40, 75], "color": "rgba(245,158,11,0.18)"},
                {"range": [75, 100], "color": "rgba(34,197,94,0.18)"},
            ],
        },
    ))
    gauge.update_layout(height=220, margin=dict(l=20, r=20, t=40, b=10))
    apply_korean_font(gauge)
    st.plotly_chart(gauge, use_container_width=True, theme=None, config={"displayModeBar": False})
with gcol2:
    donut = go.Figure(data=[go.Pie(
        labels=["검수완료", "검수미완료/미확인"],
        values=[total_done_all, total_pending_all],
        hole=0.6,
        marker=dict(colors=["#6366f1", "#e5e7eb"]),
        textinfo="percent",
        hovertemplate="%{label}: %{value:,}건<extra></extra>",
    )])
    donut.update_layout(
        height=220, margin=dict(l=10, r=10, t=10, b=10),
        showlegend=True, legend=dict(orientation="h", y=-0.1),
        annotations=[dict(text=f"{total_items_all:,}<br>문항", x=0.5, y=0.5, font_size=16, showarrow=False)],
    )
    apply_korean_font(donut)
    st.plotly_chart(donut, use_container_width=True, theme=None, config={"displayModeBar": False})

st.divider()

# ---------- 전일 대비 변경사항 ----------
st.subheader("🔄 전일 대비 변경사항", anchor=False)
DIFF_PATH = Path("data/diff_report.csv")
if DIFF_PATH.exists():
    diff_df = pd.read_csv(DIFF_PATH)
    if len(diff_df) == 0:
        st.caption("전일 대비 변경된 자료가 없습니다.")
    else:
        new_count = (diff_df["상태"] == "신규").sum()
        removed_count = (diff_df["상태"] == "삭제됨").sum()
        changed_count = (diff_df["상태"] == "변경").sum()

        d1, d2, d3, d4 = st.columns(4)
        d1.metric("신규 자료", f"{new_count}건")
        d2.metric("삭제된 자료", f"{removed_count}건")
        d3.metric("수치 변경된 자료", f"{changed_count}건")
        d4.metric("원본 문항 수 변화", f"{int(diff_df['api_item_count_변화'].sum()):+,}")

        DIFF_RENAME = {
            "book_id": "자료ID", "textbook_name": "이름", "data_type": "유형",
            "api_item_count_전일": "문항수(전일)", "api_item_count_오늘": "문항수(오늘)",
            "api_item_count_변화": "문항수 변화", "review_done_count_변화": "검수완료 변화",
            "twin_total_변화": "쌍둥이 변화", "similar_total_변화": "유사 변화",
        }
        show_cols = list(DIFF_RENAME.keys())[:3] + ["상태"] + list(DIFF_RENAME.keys())[3:]
        st.dataframe(
            diff_df[show_cols].rename(columns=DIFF_RENAME),
            use_container_width=True, hide_index=True,
        )
        st.download_button(
            "⬇ 변경사항 전체 CSV 다운로드",
            data=diff_df.to_csv(index=False).encode("utf-8-sig"),
            file_name="전일대비_변경사항.csv",
            mime="text/csv",
        )
else:
    st.caption("아직 비교할 전일 데이터가 없습니다. (다음 자동 갱신부터 생성됩니다)")

st.divider()

# ---------- 학교급별 현황 (교재+내신 통합) ----------
st.subheader("🎓 학교급별 현황 (교재+내신 통합)", anchor=False)
level_summary = (
    data.groupby("school_level")
    .agg(자료수=("book_id", "count"), 원본문항수=("api_item_count", "sum"),
         검수완료=("review_done_count", "sum"), 쌍둥이합계=("twin_total", "sum"))
    .reset_index().rename(columns={"school_level": "학교급"})
)
level_order = {"초등": 0, "중등": 1, "고등": 2, "미확인": 3}
level_summary["_order"] = level_summary["학교급"].map(level_order)
level_summary = level_summary.sort_values("_order").drop(columns="_order")
level_summary["검수완료율"] = (level_summary["검수완료"] / level_summary["원본문항수"] * 100).round(1)

lv1, lv2 = st.columns([2, 1])
with lv1:
    st.dataframe(
        level_summary, use_container_width=True, hide_index=True,
        column_config={
            "검수완료율": st.column_config.ProgressColumn("검수완료율", format="%.1f%%", min_value=0, max_value=100),
            "원본문항수": st.column_config.NumberColumn("원본문항수", format="%d"),
            "쌍둥이합계": st.column_config.NumberColumn("쌍둥이합계", format="%d"),
        },
    )
with lv2:
    fig_lv = px.bar(level_summary, x="학교급", y="원본문항수", color="학교급",
                     color_discrete_sequence=px.colors.qualitative.Pastel, text="원본문항수")
    fig_lv.update_traces(texttemplate="%{text:,}", textposition="outside")
    fig_lv.update_layout(showlegend=False, height=260, margin=dict(t=10, b=10))
    apply_korean_font(fig_lv)
    st.plotly_chart(fig_lv, use_container_width=True, theme=None, config={"displayModeBar": False})

st.divider()

tab1, tab2 = st.tabs(["📘 교재 DB 현황", "📝 내신 시험지 DB 현황"])

with tab1:
    st.subheader(f"교재 {len(books):,}권 · 원본 문항 {books['api_item_count'].sum():,}개", anchor=False)
    b1, b2, b3, b4 = st.columns(4)
    done_b = books["review_done_count"].sum()
    pending_b = books["review_pending_count"].sum()
    total_b = books["api_item_count"].sum()
    b1.metric("검수 완료", f"{done_b:,}", f"{done_b/total_b*100:.1f}%")
    b2.metric("검수 미완료", f"{pending_b:,}", f"{-pending_b/total_b*100:.1f}%", delta_color="inverse")
    b3.metric("쌍둥이 생성된 교재", f"{(books['twin_total']>0).sum()}권 / {len(books)}권")
    b4.metric("검수 100% 완료 교재", f"{(books['review_pending_count']==0).sum()}권 / {len(books)}권")

    sheet_summary = (
        books.groupby("sheet")
        .agg(교재수=("book_id", "count"), 원본문항수=("api_item_count", "sum"),
             검수완료=("review_done_count", "sum"), 쌍둥이합계=("twin_total", "sum"))
        .reset_index().rename(columns={"sheet": "분류"})
    )
    sheet_summary["검수완료율"] = (sheet_summary["검수완료"] / sheet_summary["원본문항수"] * 100).round(1)

    st.dataframe(
        sheet_summary,
        use_container_width=True, hide_index=True,
        column_config={
            "검수완료율": st.column_config.ProgressColumn(
                "검수완료율", format="%.1f%%", min_value=0, max_value=100,
            ),
            "원본문항수": st.column_config.NumberColumn("원본문항수", format="%d"),
            "쌍둥이합계": st.column_config.NumberColumn("쌍둥이합계", format="%d"),
        },
    )

    fig_a = px.bar(
        sheet_summary, x="분류", y="원본문항수", color="분류",
        color_discrete_sequence=px.colors.qualitative.Pastel,
        text="원본문항수",
    )
    fig_a.update_traces(texttemplate="%{text:,}", textposition="outside")
    fig_a.update_layout(showlegend=False, height=320, margin=dict(t=20, b=10), title="분류별 원본 문항 수")
    apply_korean_font(fig_a)
    st.plotly_chart(fig_a, use_container_width=True, theme=None, config={"displayModeBar": False})

    st.info("왼쪽 사이드바의 **교재·시험지 조회** 페이지에서 교재/내신을 한 번에 검색·필터링할 수 있습니다.")

with tab2:
    st.subheader(f"내신 시험지 {len(exams):,}건 · 원본 문항 {exams['api_item_count'].sum():,}개", anchor=False)
    e1, e2, e3, e4 = st.columns(4)
    done_e = exams["review_done_count"].sum()
    pending_e = exams["review_pending_count"].sum()
    total_e = exams["api_item_count"].sum()
    e1.metric("검수 완료", f"{done_e:,}", f"{done_e/total_e*100:.1f}%")
    e2.metric("검수 미완료/미확인", f"{pending_e:,}", f"{-pending_e/total_e*100:.1f}%", delta_color="inverse")
    e3.metric("쌍둥이 생성된 시험지", f"{(exams['twin_total']>0).sum():,}건 / {len(exams):,}건")
    e4.metric("검수 100% 완료 시험지", f"{(exams['review_pending_count']==0).sum():,}건 / {len(exams):,}건")

    col_c, col_d = st.columns(2)
    with col_c:
        region_dist = exams.groupby("지역시도").size().reset_index(name="시험지수").sort_values("시험지수", ascending=False)
        fig_c = px.bar(
            region_dist, x="지역시도", y="시험지수", color="시험지수",
            color_continuous_scale="Tealgrn",
        )
        fig_c.update_layout(height=320, margin=dict(t=20, b=10), coloraxis_showscale=False, title="시/도별 시험지 수")
        apply_korean_font(fig_c)
        st.plotly_chart(fig_c, use_container_width=True, theme=None, config={"displayModeBar": False})
    with col_d:
        year_dist = exams.groupby("연도").size().reset_index(name="시험지수")
        year_dist = year_dist[year_dist["연도"] != ""].sort_values("연도")
        fig_d = px.area(year_dist, x="연도", y="시험지수", markers=True)
        fig_d.update_traces(line_color="#6366f1", fillcolor="rgba(99,102,241,0.18)")
        fig_d.update_layout(height=320, margin=dict(t=20, b=10), title="연도별 시험지 수")
        apply_korean_font(fig_d)
        st.plotly_chart(fig_d, use_container_width=True, theme=None, config={"displayModeBar": False})

    st.info("왼쪽 사이드바의 **교재·시험지 조회** 페이지에서 지역·연도·학교별로 검색·필터링할 수 있습니다.")
