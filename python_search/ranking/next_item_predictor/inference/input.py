from __future__ import annotations

import datetime
import os

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
        hour = int(os.environ["FORCE_HOUR"]) if "FORCE_HOUR" in os.environ else now.hour
        month = (
            int(os.environ["FORCE_MONTH"]) if "FORCE_MONTH" in os.environ else now.month
        )

        instance = InferenceInput(
            hour=hour,
            month=month,
            previous_key=previous_key,
            previous_previous_key=previous_previous_key,
        )

        print("Inference input: ", instance.__dict__)

        return instance
