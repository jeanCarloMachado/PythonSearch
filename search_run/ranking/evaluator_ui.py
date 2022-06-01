import streamlit as st
import pandas as pd;

from search_run.config import ConfigurationLoader
from search_run.ranking.next_item_predictor.inference import Inference, InferenceInput

config = ConfigurationLoader().load()
keys = config.commands.keys()

from random import randrange

st.write("### Prediction results")

# result = st.selectbox('Currently Available keys', keys)
# st.write('Key name:', result)

scenarios = {

    'work vs non work same time': {
        'a': {
            'previous_key': 'ml platform roadmap team event session',
            'hour': 8,
            'month': 6,
        },
        'b': {
            'previous_key': 'but tickets to brazil',
            'hour': 8,
            'month': 6,
        }

    },
    'work in and not business hours': {
        'a': {
            'previous_key': 'ml platform roadmap team event session',
            'hour': 11,
            'month': 6,
        },
        'b': {
            'previous_key': 'ml platform roadmap team event session',
            'hour': 23,
            'month': 6,
        }

    }
}
current_scenario = st.selectbox('Scenario', scenarios)

col1, col2 = st.columns(2)


def get_input_for_scenario(scenario, a_or_b='a'):
    input_data = scenarios[scenario][a_or_b]
    return InferenceInput(**input_data)


from datetime import datetime;

col1.write("##### Input A")
inference_input = get_input_for_scenario(current_scenario, 'a')

inference_input.previous_key = col1.text_input('Previous key', inference_input.previous_key,
                                               key=datetime.now().timestamp())
col1.write(inference_input.__dict__)

results = Inference(configuration=config).get_ranking(inference_input, True)
result_df = pd.DataFrame.from_dict(results)
col1.dataframe(result_df, height=500)

col2.write("##### Input B")
inference_input = get_input_for_scenario(current_scenario, 'b')

inference_input.previous_key = col2.text_input('Previous key', inference_input.previous_key,
                                               key=datetime.now().timestamp() + 1000)
col2.write(inference_input.__dict__)

results = Inference(configuration=config).get_ranking(inference_input, True)
result_df = pd.DataFrame.from_dict(results)
col2.dataframe(result_df, height=500)
