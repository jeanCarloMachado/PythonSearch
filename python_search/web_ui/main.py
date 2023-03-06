from __future__ import annotations

import streamlit as st

from python_search.web_ui.app_functions import check_password

from python_search.web_ui.training_page import load_training_page


open_page = st.experimental_get_query_params().get("page", ["home"])[0]

def init():
    st.set_page_config(initial_sidebar_state="collapsed", layout="wide")



def sidebar():
    global open_page
    with st.sidebar:
        st.markdown(
            '<a href="?page=home" target="_self">Home</a>', unsafe_allow_html=True
        )
        st.markdown(
            '<a href="?page=entry_executed" target="_self">Entry Executed Dataset</a>', unsafe_allow_html=True
        )
        if st.button("Results evaluation"):
            open_page = "results"

        if st.button("Training Dataset"):
            open_page = "training"



def render_page():
    global open_page
    if open_page == "home":
        from python_search.web_ui.entries_page import load_homepage

        load_homepage()

    if open_page == "training":
        load_training_page()

    if open_page == "results":
        import python_search.web_ui.results_page as results_page

        results_page.load_results_page()

    if open_page == "entry_executed":
        from python_search.web_ui.entries_executed import render
        render()


if __name__ == "__main__":
    init()
    sidebar()
    if check_password():
        render_page()
