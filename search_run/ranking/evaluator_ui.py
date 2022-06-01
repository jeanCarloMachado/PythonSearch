import streamlit as st

from search_run.config import ConfigurationLoader
from search_run.ranking.next_item_predictor.inference import Inference

config = ConfigurationLoader().load()
keys = config.commands.keys()


set.write('## Keys')
st.json(list(keys))


inference = Inference(configuration=config)
