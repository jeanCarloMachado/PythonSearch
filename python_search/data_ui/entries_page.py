from __future__ import annotations

import subprocess

import streamlit as st

from python_search.data_ui.app_functions import restart_app


def extract_value_from_entry(entry):
    result = ""
    if "url" in entry:
        result = str(entry["url"])
    if "snippet" in entry:
        result = str(entry["snippet"])
    if "file" in entry:
        result = str(entry["file"])
    if "callable" in entry:
        result = str(entry["callable"])
    if "cmd" in entry:
        result = str(entry["cmd"])
    if "cli_cmd" in entry:
        result = str(entry["cli_cmd"])
    return result


def load_homepage():
    from python_search.config import ConfigurationLoader

    entries = ConfigurationLoader().load_config().commands

    col1, col2, col3 = st.columns([1, 1, 1])

    with col1:
        if st.button("Sync current host"):
            result = subprocess.check_output(
                "/src/sync_hosts.py sync", shell=True, text=True
            )
            st.write(f"Result: {result}")
            restart_app()
    with col2:
        if st.button("Restart"):
            restart_app()

    with col3:
        if st.checkbox("Add New Entry"):
            open_add_new = True
        else:
            open_add_new = False

    if open_add_new:
        key = st.text_input("Key")
        value = st.text_input("Value")
        create = st.button("Create")
        if create:
            cmd = f"python_search register_new register --key='{key}' --value='{value}' --tag=DataApp_Entry"
            st.write("Running: ", cmd)
            result = subprocess.check_output(cmd, shell=True, text=True)
            st.write(f"Result: {result}")

    st.write(" ## Entries")
    search = st.text_input("Search").lower()

    selected_tags = st.multiselect(
        "Tags", ConfigurationLoader().load_config().get_default_tags()
    )
    has_filter = len(search) > 0 or len(selected_tags) > 0
    limit = 50 if not has_filter else None

    rendered = 0
    for key, value in entries.items():
        if limit and rendered > limit:
            break

        value_str = extract_value_from_entry(value)
        tags = " ".join(value.get("tags", []))

        if not set(selected_tags).issubset(set(value.get("tags", []))):
            continue

        if (
            search
            and (search not in key)
            and search not in value_str
            and search not in tags
        ):
            continue

        col_key, col_value, col_tags = st.columns((1, 2, 1))
        col_key.write(key)
        col_value.write(value_str)
        col_tags.write(tags)

        rendered += 1
    st.write(f"**Total entries displayed**: {rendered}")
