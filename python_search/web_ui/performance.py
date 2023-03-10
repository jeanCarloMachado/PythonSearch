import pandas as pd
import streamlit as st

from python_search.events.run_performed.dataset import EntryExecutedDataset


def render():
    search_performed_df = EntryExecutedDataset().load_new()
    df = search_performed_df.toPandas()

    df["time"] = pd.to_datetime(df["timestamp"], unit="s")
    df.set_index("time", inplace=True)
    df["after_execution_time"] = pd.to_datetime(df["after_execution_time"])
    df["earliest_time"] = pd.to_datetime(df["earliest_time"])

    df = df.loc["2023-03-09":]

    df["diff"] = df["after_execution_time"] - df["earliest_time"]
    df["diff"] = df["diff"].dt.total_seconds()

    df = df[["diff"]]

    st.write("## Seconds from start execution to run key")
    st.line_chart(df)
