import pandas as pd
import streamlit as st

from python_search.events.run_performed.dataset import EntryExecutedDataset


def render():
    st.write("## Entry Executed overview")
    search_performed_df = EntryExecutedDataset().load_new()
    df = search_performed_df.toPandas()

    df["time"] = pd.to_datetime(df["timestamp"], unit="s")

    st.dataframe(df)

    st.write("## Base Schemas")
    st.write(search_performed_df.schema)
    st.write(df.dtypes)

    st.write("## Summary ")
    st.write(df.describe())

    df["time_index"] = df["time"]
    df.set_index("time_index", inplace=True)
    st.write("## Entry executed timeline by hour")
    timeseries = df.groupby(pd.Grouper(freq="1H")).count()["key"]
    # st.write(timeseries)
    st.line_chart(timeseries)

    st.write("## Ranking position")
    st.line_chart(df["rank_position"])
