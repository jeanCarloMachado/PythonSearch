from __future__ import annotations

import streamlit as st


from python_search.data_ui.app_functions import check_password
from python_search.events.run_performed.dataset import EntryExecutedDataset

from python_search.data_ui.training_page import load_training_page

open_page = "home"
def init():
    st.set_page_config(initial_sidebar_state="collapsed", layout="wide")

def sidebar():
    global open_page
    with st.sidebar:

        if st.button("HomePage"):
            open_page = "home"

        if st.button("Results evaluation"):
            open_page = "results"

        if st.button("Training Dataset"):
            open_page = "training"

        if st.button("Searches Performed Dataset"):
            open_page = "searches_performed_dataset"


def render_page():
    global open_page
    if open_page == "home":
        from python_search.data_ui.entries_page import load_homepage

        load_homepage()

    if open_page == "training":
        load_training_page()

    if open_page == "results":
        import python_search.data_ui.results_page as results_page

        results_page.load_results_page()

    if open_page == "searches_performed_dataset":
        st.write("## Searches performed dataset")
        search_performed_df = EntryExecutedDataset().load_clean()
        pdf = search_performed_df.toPandas()
        st.dataframe(pdf)


if __name__ == '__main__':
    init()
    sidebar()
    if check_password():
        render_page()
