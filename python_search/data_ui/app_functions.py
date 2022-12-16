from __future__ import annotations

import os
import subprocess

import streamlit as st


def restart_app():
    result = subprocess.check_output("pkill streamlit", shell=True, text=True)
    st.write(f"Result: {result}")


import streamlit as st


def check_password():
    """Returns `True` if the user had the correct password."""

    if "PS_DISABLE_PASSWORD" in os.environ:
        print("Password disabled")
        return True

    def password_entered():
        import os

        """Checks whether a password entered by the user is correct."""
        if st.session_state["password"] == os.environ["PS_WEB_PASSWORD"]:
            st.session_state["password_correct"] = True
            del st.session_state["password"]  # don't store password
        else:
            st.session_state["password_correct"] = False

    if "password_correct" not in st.session_state:
        # First run, show input for password.
        st.text_input(
            "Password", type="password", on_change=password_entered, key="password"
        )
        return False
    elif not st.session_state["password_correct"]:
        # Password not correct, show input + error.
        st.text_input(
            "Password", type="password", on_change=password_entered, key="password"
        )
        st.error("😕 Password incorrect")
        return False
    else:
        # Password correct.
        return True
