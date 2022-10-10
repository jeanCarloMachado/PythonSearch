from __future__ import annotations

import os
from collections import namedtuple
from typing import List, Optional, Tuple

from python_search.config import PythonSearchConfiguration
from python_search.feature_toggle import FeatureToggle
from python_search.infrastructure.performance import timeit
from python_search.infrastructure.redis import PythonSearchRedis
from python_search.observability.logger import logging
from python_search.ranking.results import FzfOptimizedSearchResults

ModelInfo = namedtuple("ModelInfo", "features label")


class RankingGenerator:
    """
    Generates the ranking for python search
    """

    NUMBER_OF_LATEST_ENTRIES = 7

    _model_info = ModelInfo(["position", "key_lenght"], "input_lenght")

    def __init__(self, configuration: Optional[PythonSearchConfiguration] = None):
        self._configuration = configuration
        self._feature_toggle = FeatureToggle()
        self._model = None
        self._debug = os.getenv("DEBUG", False)
        self._entries_result = FzfOptimizedSearchResults()

        if self._configuration.supported_features.is_redis_supported():
            self.redis_client = PythonSearchRedis.get_client()

        self.used_entries: List[Tuple[str, dict]] = []

        if self._feature_toggle.is_enabled("ranking_next"):
            from python_search.ranking.next_item_predictor.inference.inference import \
                Inference

            self.inference = Inference(self._configuration)

    @timeit
    def generate(self, print_entries=True, print_weights=False) -> str:
        """
        Recomputes the rank and saves the results on the file to be read
        """

        self._entries: dict = self._configuration.commands
        # by default the rank is just in the order they are persisted in the file
        self.ranked_keys: List[str] = self._entries.keys()

        if self._feature_toggle.is_enabled("ranking_next"):
            self.ranked_keys = self.inference.get_ranking(print_weights=print_weights)

        """Populate the variable used_entries  with the results from redis"""
        self._fetch_latest_entries()
        result, only_list = self._merge_and_build_result()

        if not print_entries:
            return

        return self._entries_result.build_entries_result(result)

    def _save_ranking_order_in_cache(self, ranking: List[str]):
        encoded_list = "|".join(ranking)
        self.redis_client.set("cache_ranking_result", encoded_list)

    def _can_load_from_cache(self):
        return (
            self._configuration.supported_features.is_redis_supported()
            and self._configuration.supported_features.is_dynamic_ranking_supported()
        )

    def _merge_and_build_result(self) -> List[Tuple[str, dict]]:
        """ "
        Merge the ranking with the latest _entries and make it ready to be printed
        """
        result = []
        increment = 0
        final_key_list = []

        while self.used_entries:
            used_entry = self.used_entries.pop()
            key = used_entry[0]
            if key not in self._entries:
                # key not found in _entries
                continue

            # sometimes there can be a bug of saving somethign other than dicts as _entries
            if type(used_entry[1]) != dict:
                logging.warning(f"Entry is not a dict {used_entry[1]}")
                continue
            logging.debug(f"Increment: {increment}  with entry {used_entry}")
            final_key_list.append(used_entry[0])
            result.append((used_entry[0], {**used_entry[1], "recently_used": True}))
            increment += 1

        for key in self.ranked_keys:
            if key not in self._entries:
                # key not found in _entries
                continue

            result.append((key, self._entries[key]))
            final_key_list.append(key)
            increment += 1

        # the result is the one to be returned, final_key_list is to be used in the cache
        return result, final_key_list

    def _fetch_latest_entries(self):
        """Populate the variable used_entries  with the results from redis"""
        self.used_entries: List[Tuple[str, dict]] = []
        if not self._configuration.supported_features.is_enabled(
            "redis"
        ) or not self._feature_toggle.is_enabled("ranking_latest_used"):
            if self._debug:
                print(f"Disabled latest _entries")
            return

        self.used_entries = self.get_used_entries_from_redis(self._entries)
        # only use the latest 7 _entries for the top of the ranking
        self.used_entries = self.used_entries[-self.NUMBER_OF_LATEST_ENTRIES :]

        if self._debug:
            print(f"Used _entries: {self.used_entries}")

    def get_used_entries_from_redis(self, entries) -> List[Tuple[str, dict]]:
        """
        returns a list of used _entries to be placed on top of the ranking
        """
        used_entries = []
        latest_used = self._get_latest_used_keys()
        for used_key in latest_used:
            if used_key not in entries or used_key in used_entries:
                continue
            used_entries.append((used_key, entries[used_key]))
        # reverse the list given that we pop from the end
        used_entries.reverse()
        return used_entries

    def _get_latest_used_keys(self):
        from python_search.events.latest_used_entries import RecentKeys

        return RecentKeys().get_latest_used_keys()


if __name__ == "__main__":
    import fire

    fire.Fire()
