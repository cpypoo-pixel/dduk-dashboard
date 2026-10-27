# -*- coding: utf-8 -*-
"""대시보드 공통 스타일(애니메이션/카드 효과)을 모든 페이지에서 재사용."""
import streamlit as st

CUSTOM_CSS = """
<style>
@keyframes fadeInUp {
  from { opacity: 0; transform: translateY(14px); }
  to { opacity: 1; transform: translateY(0); }
}
@keyframes popIn {
  0% { opacity: 0; transform: scale(0.92); }
  70% { opacity: 1; transform: scale(1.02); }
  100% { opacity: 1; transform: scale(1); }
}
.block-container { animation: fadeInUp 0.5s ease-out; }
div[data-testid="stMetric"] {
  background: linear-gradient(135deg, rgba(99,102,241,0.08), rgba(236,72,153,0.06));
  border: 1px solid rgba(99,102,241,0.18);
  border-radius: 14px;
  padding: 14px 16px 10px 16px;
  animation: popIn 0.45s ease-out;
  transition: transform 0.18s ease, box-shadow 0.18s ease, border-color 0.18s ease;
}
div[data-testid="stMetric"]:hover {
  transform: translateY(-3px);
  box-shadow: 0 8px 20px rgba(99,102,241,0.18);
  border-color: rgba(99,102,241,0.45);
}
[data-testid="stDataFrame"] {
  animation: fadeInUp 0.6s ease-out;
  border-radius: 10px;
  overflow: hidden;
}
[data-testid="stTabs"] button {
  transition: color 0.15s ease, transform 0.15s ease;
}
[data-testid="stTabs"] button:hover { transform: translateY(-1px); }
div[data-testid="stSelectbox"], div[data-testid="stTextInput"] {
  transition: transform 0.15s ease;
}
hr { opacity: 0.35; }
</style>
"""


def inject():
    st.markdown(CUSTOM_CSS, unsafe_allow_html=True)


# Plotly 기본 폰트가 일부 한글 글리프를 지원하지 않아 글자가 깨져 보이는 문제 방지
PLOTLY_FONT = "Malgun Gothic, Apple SD Gothic Neo, Noto Sans KR, sans-serif"


def apply_korean_font(fig):
    fig.update_layout(font=dict(family=PLOTLY_FONT))
    return fig
