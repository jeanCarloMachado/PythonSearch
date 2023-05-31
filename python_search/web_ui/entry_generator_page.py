import streamlit as st

from python_search.configuration.loader import ConfigurationLoader
from python_search.core_entities.core_entities import Entry
from python_search.data_exporter import DataExporter


def render():
    entries = ConfigurationLoader().load_config().commands
    st.write(len(entries))
    entries = DataExporter().filter_out_blacklisted(entries)
    st.write(len(entries))
    import pandas as pd

    pandas_df = pd.DataFrame()

    pandas_df["prompt"] = entries.keys()
    completion = [
        f"{Entry(key, value).get_content_str()} | {Entry(key, value).get_type_str()}"
        for key, value in entries.items()
    ]
    pandas_df["completion"] = completion

    st.write(pandas_df)

    if st.button("Write"):
        with open("/tmp/records.jsonl", "w") as f:
            f.write(pandas_df.to_json(orient="records", lines=True))
        st.success("Done")
