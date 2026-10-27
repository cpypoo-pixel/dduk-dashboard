# -*- coding: utf-8 -*-
"""비밀번호 보호. 외부에서도 접근 가능하게 배포하기 때문에 최소한의 접근 통제를 둔다."""
import streamlit as st


def require_login():
    if st.session_state.get("authed"):
        return

    st.title("🔒 로그인 필요")
    pw = st.text_input("비밀번호", type="password")
    if st.button("입장"):
        if pw == st.secrets.get("password"):
            st.session_state["authed"] = True
            st.rerun()
        else:
            st.error("비밀번호가 틀렸습니다.")
    st.stop()
