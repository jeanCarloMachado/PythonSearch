import streamlit as st

from python_search.events.run_performed.dataset import EntryExecutedDataset


def render():
    st.write("## Searches performed dataset")
    search_performed_df = EntryExecutedDataset().load_new()
    df = search_performed_df.toPandas()


    st.write(df.describe())
    st.dataframe(df)
