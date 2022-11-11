from __future__ import annotations

import datetime
import os
from typing import Optional

from python_search.search.next_item_predictor.features.times_used import TimesUsed


class ModelInput:
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
        times_used_previous: Optional[int] = None,
        times_used_previous_previous: Optional[int] = None,
    ):
        self.hour = hour
        self.month = month
        self.previous_key = previous_key
        self.previous_previous_key = previous_previous_key
        self.times_used_previous = times_used_previous
        self.times_used_previous_previous = times_used_previous_previous

        if not ModelInput._times_used:
            ModelInput._times_used = TimesUsed()

        if not times_used_previous:
            self.times_used_previous = ModelInput._times_used.get_value(previous_key)
        if not times_used_previous_previous:
            self.times_used_previous_previous = ModelInput._times_used.get_value(
                previous_previous_key
            )

    @staticmethod
    def with_given_keys(previous_key: str, previous_previous_key: str) -> "ModelInput":
        """
        Do inference based on the current time and the recent used keys
        """
        now = datetime.datetime.now()
        hour = int(os.environ["FORCE_HOUR"]) if "FORCE_HOUR" in os.environ else now.hour
        month = (
            int(os.environ["FORCE_MONTH"]) if "FORCE_MONTH" in os.environ else now.month
        )

        instance = ModelInput(
            hour=hour,
            month=month,
            previous_key=previous_key,
            previous_previous_key=previous_previous_key,
        )

        print("Inference input: ", instance.__dict__)

        return instance
