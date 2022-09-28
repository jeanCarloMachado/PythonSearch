from __future__ import annotations

import datetime
import os
from typing import Optional

from python_search.ranking.next_item_predictor.features.times_used import \
    TimesUsed
from python_search.ranking.next_item_predictor.inference.embeddings_loader import \
    InferenceEmbeddingsLoader


class InferenceInput:
    hour: int
    month: int
    previous_key: str
    previous_previous_key: str
    times_used_previous: int
    times_used_previous_previous: int

    _times_used: Optional[TimesUsed] = None

    def __init__(
        self,
        *,
        hour,
        month,
        previous_key,
        previous_previous_key,
        times_used_previous=None,
        times_used_previous_previous=None,
    ):
        self.hour = hour
        self.month = month
        self.previous_key = previous_key
        self.previous_previous_key = previous_previous_key
        self.times_used_previous = times_used_previous
        self.times_used_previous_previous = times_used_previous_previous

        if not InferenceInput._times_used:
            InferenceInput._times_used = TimesUsed()

        if not times_used_previous:
            self.times_used_previous = InferenceInput._times_used.item_popularity(
                previous_key
            )
        if not times_used_previous_previous:
            self.times_used_previous_previous = (
                InferenceInput._times_used.item_popularity(previous_previous_key)
            )

    @staticmethod
    def with_given_keys(
        previous_key: str, previous_previous_key: str
    ) -> "InferenceInput":
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
