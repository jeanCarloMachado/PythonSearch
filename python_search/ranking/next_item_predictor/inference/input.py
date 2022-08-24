from __future__ import annotations

import datetime

from python_search.ranking.next_item_predictor.inference.embeddings_loader import \
    InferenceEmbeddingsLoader


class InferenceInput:
    hour: int
    month: int
    previous_key: str

    def __init__(self, *, hour, month, previous_key):
        self.hour = hour
        self.month = month
        self.previous_key = previous_key

    @staticmethod
    def with_key(recent_key: str) -> "InferenceInput":
        """
        Do inference based on the current time and the recent used keys
        """
        now = datetime.datetime.now()

        instance = InferenceInput(
            hour=now.hour, month=now.month, previous_key=recent_key
        )

        print("Inference input: ", instance.__dict__)

        return instance
