from __future__ import annotations

import subprocess

import pandas as pd
import streamlit as st

from python_search.data_ui.app_functions import restart_app
from python_search.entry_capture.register_new import RegisterNew


def load_homepage():
    from python_search.config import ConfigurationLoader

    entries = ConfigurationLoader().load_config().commands

    if st.button("Sync hosts"):
        result = subprocess.check_output('/src/sync_hosts.sh ', shell=True, text=True)
        st.write(f"Result: {result}")
        restart_app()
    if st.button("Restart"):
        restart_app()

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

    st.dataframe(df.head(50))
