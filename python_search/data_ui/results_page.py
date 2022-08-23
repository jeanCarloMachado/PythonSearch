def load_results_page():
    import pandas as pd
    import streamlit as st

    from python_search.config import ConfigurationLoader

    config = ConfigurationLoader().load()

    keys = config.commands.keys()

    from python_search.ranking.next_item_predictor.inference.inference import \
        Inference
    from python_search.ranking.next_item_predictor.inference.input import \
        InferenceInput

    st.write("### Prediction results")
    st.write("##### Model run: " + Inference.PRODUCTION_RUN_ID)

    scenarios = {
        "work vs non work typical hours": {
            "a": {
                "previous_key": "ml platform roadmap team event session",
                "hour": 14,
                "month": 6,
            },
            "b": {
                "previous_key": "but tickets to brazil",
                "hour": 21,
                "month": 6,
            },
        },
        "work vs non work typical hours 2": {
            "a": {
                "previous_key": "git log in catalog",
                "hour": 14,
                "month": 6,
            },
            "b": {
                "previous_key": "precos agosto enviado ao pai",
                "hour": 21,
                "month": 6,
            },
        },
        "work in and not business hours": {
            "a": {
                "previous_key": "ml platform roadmap team event session",
                "hour": 11,
                "month": 6,
            },
            "b": {
                "previous_key": "ml platform roadmap team event session",
                "hour": 23,
                "month": 6,
            },
        },
    }
    current_scenario = st.selectbox("Scenario", scenarios)

    colA, colB = st.columns(2)

    def get_inference_input_for_scenario(scenario, a_or_b="a") -> InferenceInput:
        input_data = scenarios[scenario][a_or_b]
        return InferenceInput(**input_data)

    def perform_inference(inference_input):
        results = Inference(configuration=config).get_ranking(inference_input, True)
        return pd.DataFrame.from_dict(results)

    colA.write("##### Input A")
    inference_a = get_inference_input_for_scenario(current_scenario, "a")

    inference_a.previous_key = colA.text_input(
        "Previous key A", inference_a.previous_key
    )
    colA.write(inference_a.__dict__)
    colA.dataframe(perform_inference(inference_a), height=500)

    colB.write("##### Input B")
    inference_b = get_inference_input_for_scenario(current_scenario, "b")

    inference_b.previous_key = colB.text_input(
        "Previous key B", inference_b.previous_key
    )
    colB.write(inference_b.__dict__)
    colB.dataframe(perform_inference(inference_b), height=500)
