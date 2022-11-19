from __future__ import annotations
import pandas as pd

import streamlit as st

from python_search.entry_capture.register_new import RegisterNew
from python_search.events.run_performed.dataset import RunPerformedDataset

from python_search.data_ui.training_page import load_training_page

open_page = "home"

with st.sidebar:

    if st.button("Home"):
        open_page = "home"

    if st.button("Results evaluation"):
        open_page = "results"

    if st.button("Training Dataset"):
        open_page = "training"

    if st.button("Searches Performed Dataset"):
        open_page = "searches_performed_dataset"


if open_page == 'home':
    from python_search.config import ConfigurationLoader

    entries = ConfigurationLoader().load_config().commands

    if st.button("Sync hosts"):
        import subprocess
        result = subprocess.check_output('/src/sync_hosts.sh ', shell=True, text=True)
        st.write(f"Result: {result}")

    if st.checkbox("Add new entry"):
        key = st.text_input("Key")
        value = st.text_input("Value")
        create = st.button("Create")
        if create:
            RegisterNew().register(key=key, value=value)
            config = ConfigurationLoader().load_config()
            entries = config.commands


    search = st.text_input('Search').lower()
    data = []
    for key, value in entries.items():
        data.append((key, value))

    st.write("## Entries ")
    df = pd.DataFrame.from_records(data, columns=['key', 'value'])

    if search:
        df.query('key.str.contains(@search) or value.str.contains(@search)', inplace=True)

    st.dataframe(df)


if open_page == "training":
    load_training_page()

if open_page == "results":
    import python_search.data_ui.results_page as results_page

    results_page.load_results_page()

if open_page == "searches_performed_dataset":
    st.write("## Searches performed dataset")
    search_performed_df = RunPerformedDataset().load_clean()
    pdf = search_performed_df.toPandas()
    st.dataframe(pdf)
