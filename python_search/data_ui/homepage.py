from __future__ import annotations

import subprocess

import pandas as pd
import streamlit as st

from python_search.data_ui.app_functions import restart_app
from python_search.entry_capture.register_new import RegisterNew

def extract_value_from_entry(entry):
    result = ""
    if 'url' in entry:
        result = entry['url']
    if 'snippet' in entry:
        result = entry['snippet']
    if 'file' in entry:
        result = entry['file']
    if 'callable' in entry:
        result = str(entry['callable'])
    if 'cmd' in entry:
        result = entry['cmd']
    if 'cli_cmd' in entry:
        result = entry['cli_cmd']
    return result

def load_homepage():
    from python_search.config import ConfigurationLoader

    entries = ConfigurationLoader().load_config().commands

    col1, col2, col3  = st.columns([1, 1, 1])

    with col1:
        if st.button("Sync hosts"):
            result = subprocess.check_output('/src/sync_hosts.sh ', shell=True, text=True)
            st.write(f"Result: {result}")
            restart_app()
    with col2:
        if st.button("Restart"):
            restart_app()

    with col3:
        if st.checkbox("Add new entry"):
            open_add_new =  True
        else:
            open_add_new =  False


    if open_add_new:
        key = st.text_input("Key")
        value = st.text_input("Value")
        create = st.button("Create")
        if create:
            RegisterNew().register(key=key, value=value)
            restart_app()

    search = st.text_input('Search').lower()
    data = []
    limit = 50
    rendered = 0

    st.write(" ## Entries")
    for key, value in entries.items():
        if rendered > limit:
            break

        value = extract_value_from_entry(value)
        if search and (search not in key) and search not in value:
            continue
        col_key, col_value = st.columns((1, 3))
        col_key.write(key)
        col_value.write(value)

        rendered += 1
