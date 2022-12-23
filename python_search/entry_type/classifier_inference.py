from __future__ import annotations
import json
import uuid
from typing import Optional, Tuple

import numpy as np
from pydantic import BaseModel

from python_search.entry_type.entity import EntryType
from python_search.infrastructure.arize import Arize

PredictionUuid = str


class PredictEntryTypeInference:
    PRODUCTION_RUN_ID = "004224c854464ec296b5f648bd3f74f5"

    def __init__(self):
        # Instantiate an Arize Client object using your API and Space keys
        self._arize_client = Arize().get_client()

    def predict_entry_type_from_dict(self, entry: dict) -> EntryType:
        return self.predict_entry_type(EntryData(**entry))

    def predict_entry_type(
        self, entry_data: EntryData
    ) -> Tuple[EntryType, PredictionUuid]:

        from python_search.search.models import PythonSearchMLFlow

        model = PythonSearchMLFlow().get_entry_type_classifier(
            run_id=PredictEntryTypeInference.PRODUCTION_RUN_ID
        )
        from python_search.search.next_item_predictor.features.entry_embeddings.entry_embeddings import (
            create_embeddings_from_strings,
        )

        data = create_embeddings_from_strings([entry_data.content])

        from python_search.entry_type.entry_type_pipeline import Pipeline

        X = np.zeros([1, Pipeline.INPUT_DIMENSIONS])

        has_pipe = "|" in entry_data.content
        has_double_minus = "--" in entry_data.content

        X[0] = np.concatenate(
            (
                data[0],
                np.asarray([1 if has_pipe else 0]),
                np.asarray([1 if has_double_minus else 0]),
            )
        )

        result = model.predict(X)
        value, prediction_label = get_value_and_label(result[0])

        prediction_uuid = str(uuid.uuid4())
        if Arize.is_installed():
            from arize.utils.types import ModelTypes, Environments, Embedding

            arize_result = self._arize_client.log(
                model_id=Arize.MODEL_ID,
                model_version=Arize.MODEL_VERSION,
                model_type=ModelTypes.SCORE_CATEGORICAL,
                environment=Environments.PRODUCTION,
                prediction_id=prediction_uuid,
                features={"has_pipe": has_pipe, "has_double_minus": has_double_minus},
                embedding_features={
                    "content": Embedding(vector=data[0], data=entry_data.content)
                },
                prediction_label=(prediction_label, float(value)),
            )
            Arize.arize_responses_helper(arize_result)

        print("Predicted label: ", prediction_label)

        return prediction_label, prediction_uuid


class ClassifierInferenceClient:
    def predict_from_content(self, content: str):
        return self.predict(EntryData(content=content))

    def predict(self, data: EntryData) -> Optional[Tuple[EntryType, PredictionUuid]]:
        import requests

        try:
            result = requests.post(
                url="http://localhost:8000/entry_type/classify", json=data.__dict__
            )
            data = json.loads(result.text)
            return data["predicted_type"], data["prediction_uuid"]
        except BaseException as e:
            print(f"Logging results failed, reason: {e}")
            return None


def get_value_and_label(prediction_result) -> Tuple[float, EntryType]:
    max_val = max(prediction_result)

    for k, v in enumerate(prediction_result):
        if max_val == v:
            result = EntryType.from_categorical(k)
            break
    return max_val, result.value


class EntryData(BaseModel):
    content: str
    key: Optional[str]


def main():
    import fire

    fire.Fire()


if __name__ == "__main__":
    main()
