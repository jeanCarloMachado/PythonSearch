import glob
import logging
from typing import Any, Dict, List

import pandas as pd

from search_run.data_paths import DataPaths
from search_run.observability.logger import configure_logger

logger = configure_logger()


class CiclicalPlacement:
    """
    Joins multiple ranking methods and place them in clycles
    """

    def cyclical_placment(
        self, entries: Dict, head_keys: List[str], commands_performed
    ) -> List[Any]:
        """Put 1 result of natural rank after 1 result of visits"""

        self.head_keys = head_keys
        # reverse the keys so on pop we get the first one
        self.head_keys.reverse()
        self.natural_position: List[str] = self.compute_natural_position_scores(entries)
        self.used_items: List[str] = self.compute_used_items_score(
            entries, commands_performed
        )
        model_key_lenght_prediction = glob.glob(
            DataPaths.prediction_batch_location + "/*.csv"
        )
        self.input_lenght_df = pd.read_csv(model_key_lenght_prediction[0])
        self.entries = entries

        all_keys = list(entries.keys())
        result = []
        self.used_keys: List[str] = []
        position = 0

        # make the first result be the last executed
        while all_keys:
            key = self.get_next_key(position)
            logger.debug(f"Add key {key}")
            position = position + 1
            if key in self.used_keys:
                logging.debug(f"Key {key} already in used items")
                continue

            if not key in entries:
                logger.debug(f"Key not in entries {key}")
                continue

            entry_data = entries[key]
            result.append((key, entry_data))

            self.used_keys.append(key)
            all_keys.remove(key)

        return result

    def get_next_key(self, position):
        while self.head_keys:

            key = self.head_keys.pop()
            logging.debug(f"popping head keys {key}")
            return key

        if position % 2 == 0 and len(self.used_items) > 0:
            for key in self.natural_position[:]:
                self.natural_position.remove(key)
                if key not in self.used_keys:
                    return key

        if position % 3 == 0 and len(self.input_lenght_df) > 0:
            while True and len(self.input_lenght_df):
                key = self.input_lenght_df.iloc[0]["key"]
                self.input_lenght_df = self.input_lenght_df.iloc[1:]
                return key

        for key in self.natural_position:
            self.natural_position.remove(key)
            if key not in self.used_keys[:]:
                return key

    def compute_used_items_score(self, entries, commands_performed):
        # a list with the keys of used entries, separated by space
        used_items = commands_performed["key"].tolist()

        # linear decay for use
        total_used_items = len(used_items)
        scores_used_items = {}
        for position, key in enumerate(used_items):
            if key not in entries:
                logger.debug(f"key not in entries: {key}")
                continue

            score = (total_used_items - position) / total_used_items

            if key in scores_used_items:
                aggregation = score + (scores_used_items[key] * (1 / position))
                score = aggregation if aggregation < 1 else 1

            scores_used_items[key] = score
        used_items = sorted(scores_used_items, key=scores_used_items.get, reverse=True)

        return used_items

    def compute_natural_position_scores(self, entries):
        # quadratic decay for position
        total_items = len(entries)
        natural_position_scored = {}
        for position, (key, value) in enumerate(entries.items()):
            natural_position_scored[key] = total_items / (total_items + position)

        natural_position = sorted(
            natural_position_scored, key=natural_position_scored.get, reverse=True
        )

        return natural_position
