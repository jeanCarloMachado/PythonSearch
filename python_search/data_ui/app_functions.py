from __future__ import annotations

import subprocess

import streamlit as st


def restart_app():
    result = subprocess.check_output('pkill streamlit', shell=True, text=True)
    st.write(f"Result: {result}")
