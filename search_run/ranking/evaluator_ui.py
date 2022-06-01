import streamlit as st
import pandas as pd;

from search_run.config import ConfigurationLoader
from search_run.ranking.next_item_predictor.inference import Inference, InferenceInput

config = ConfigurationLoader().load()
keys = config.commands.keys()

from random import randrange
#st.write('## Keys')
#st.json(list(keys))
st.write("### Prediction results")

result = st.selectbox('Currently Available keys', keys)
st.write('Key name:', result)

col1, col2 = st.columns(2)



def show_rank(inference_iput: InferenceInput, col):
    col.write("##### Input")
    inference_iput.previous_key = col.text_input('Previous key', inference_iput.previous_key,key=randrange(100000))
    col.write(predefined_input.__dict__)

    results = Inference(configuration=config).get_ranking(predefined_input, True)
    result_df = pd.DataFrame.from_dict(results)
    col.dataframe(result_df, height=500)

predefined_input = InferenceInput(hour=12, month=6, previous_key='new gyg core values')
show_rank(predefined_input, col1)


predefined_input = InferenceInput(hour=12, month=6, previous_key='location ozora')
show_rank(predefined_input, col2)
