from __future__ import annotations

import os

import streamlit as st

from python_search.data_ui.training_page import load_training_page
from python_search.events.search_run_performed.searchesperformeddataset import \
    SearchesPerformedDataset

open_page = "results"

os.putenv("SPARK_LOCAL_IP", "localhost")
with st.sidebar:

    if st.button("Results evaluation"):
        open_page = "results"

    if st.button("Training Dataset"):
        open_page = "training"

    if st.button("Searches Performed Dataset"):
        open_page = "searches_performed_dataset"


if open_page == "training":
    load_training_page()

if open_page == "results":
    import python_search.data_ui.results_page as results_page

    results_page.load_results_page()

if open_page == "searches_performed_dataset":
    st.write("## Searches performed dataset")
    search_performed_df = SearchesPerformedDataset().load_clean()
    pdf = search_performed_df.toPandas()
    st.dataframe(pdf)
