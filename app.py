# -*- coding: utf-8 -*-
"""앱 진입점. 사이드바 메뉴 이름/아이콘을 여기서 직접 지정한다."""
import streamlit as st

st.set_page_config(page_title="DB 통합 대시보드", layout="wide", page_icon="📊")

pg = st.navigation([
    st.Page("views/dashboard.py", title="DB 통합 대시보드", icon="📊", default=True),
    st.Page("pages/1_교재_시험지_조회.py", title="교재·시험지 조회", icon="🔍"),
    st.Page("pages/9_샘플교재_최상위수학라이트.py", title="샘플교재 최상위수학라이트", icon="📘"),
])
pg.run()
