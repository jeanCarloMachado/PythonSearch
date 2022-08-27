from __future__ import annotations

import datetime

from python_search.ranking.next_item_predictor.inference.embeddings_loader import \
    InferenceEmbeddingsLoader


class InferenceInput:
    hour: int
    month: int
    previous_key: str
    previous_previous_key: str

    def __init__(self, *, hour, month, previous_key, previous_previous_key):
        self.hour = hour
        self.month = month
        self.previous_key = previous_key
        self.previous_previous_key = previous_previous_key

    @staticmethod
    def with_keys(previous_key: str, previous_previous_key: str) -> "InferenceInput":
        """
        Do inference based on the current time and the recent used keys
        """
        now = datetime.datetime.now()

        instance = InferenceInput(
            hour=now.hour,
            month=now.month,
            previous_key=previous_key,
            previous_previous_key=previous_previous_key,
        )

        print("Inference input: ", instance.__dict__)

        return instance
