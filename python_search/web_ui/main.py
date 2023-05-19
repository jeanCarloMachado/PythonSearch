from __future__ import annotations

import streamlit as st

from app_functions import check_password

from training_page import load_training_page


open_page = st.experimental_get_query_params().get("page", ["home"])[0]


def init():
    st.set_page_config(layout="wide")


def sidebar():
    global open_page
    with st.sidebar:
        st.markdown(
            '<a href="?page=home" target="_self">Home</a>', unsafe_allow_html=True
        )
        st.markdown(
            '<a href="?page=entry_executed" target="_self">Entry Executed Dataset</a>',
            unsafe_allow_html=True,
        )
        st.markdown(
            '<a href="?page=entrygenerator" target="_self">Entry generator</a>',
            unsafe_allow_html=True,
        )
        st.markdown(
            '<a href="?page=performance" target="_self">Performance</a>',
            unsafe_allow_html=True,
        )


def render_page():
    global open_page
    if open_page == "home":
        from entries_page import load_homepage

        load_homepage()

    if open_page == "training":
        load_training_page()

    if open_page == "results":
        import results_page as results_page

        results_page.load_results_page()

    if open_page == "entry_executed":
        from entry_executed import render

        render()

    if open_page == "entrygenerator":
        from entry_generator_page import render

        render()

    if open_page == "performance":
        from performance import render

        render()


if __name__ == "__main__":
    init()
    sidebar()
    if check_password():
        render_page()
