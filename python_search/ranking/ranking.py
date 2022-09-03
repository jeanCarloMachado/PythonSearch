from __future__ import annotations

import json
import os
from collections import namedtuple
from typing import List, Optional, Tuple

from python_search.acronyms import generate_acronyms
from python_search.config import PythonSearchConfiguration
from python_search.features import FeatureToggle
from python_search.infrastructure.performance import timeit
from python_search.infrastructure.redis import PythonSearchRedis
from python_search.observability.logger import logging

ModelInfo = namedtuple("ModelInfo", "features label")


class RankingGenerator:
    """
    Generates the ranking for python search
    """

    _model_info = ModelInfo(["position", "key_lenght"], "input_lenght")

    def __init__(self, configuration: Optional[PythonSearchConfiguration] = None):
        self._configuration = configuration
        self._feature_toggle = FeatureToggle()
        self._model = None
        self._debug = os.getenv("DEBUG", False)
        self._entries_result = SearchableEntriesResult()

        if self._configuration.supported_features.is_redis_supported():
            self.redis_client = PythonSearchRedis.get_client()

        self.used_entries: List[Tuple[str, dict]] = []

        if self._feature_toggle.is_enabled("ranking_next"):
            from python_search.ranking.next_item_predictor.inference.inference import \
                Inference

            self.inference = Inference(self._configuration)

    def generate_with_caching(self):
        """
        Uses cached rank if available and only add new keys on top
        """
        self.generate(recompute_ranking=False)

    @timeit
    def generate(self, print_entries=True, print_weights=False):
        """
        Recomputes the rank and saves the results on the file to be read
        """

        self.entries: dict = self._configuration.commands
        # by default the rank is just in the order they are persisted in the file
        self.ranked_keys: List[str] = self.entries.keys()

        try:
            """Mutate self.ranked keys with the results"""
            self.ranked_keys = self.inference.get_ranking(print_weights=print_weights)
        except Exception as e:
            print(f"Inference failed with error {e} falling back to default ranking")

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
        Merge the ranking with the latest entries and make it ready to be printed
        """
        result = []
        increment = 0
        final_key_list = []

        while self.used_entries:
            used_entry = self.used_entries.pop()
            key = used_entry[0]
            if key not in self.entries:
                # key not found in entries
                continue

            # sometimes there can be a bug of saving somethign other than dicts as entries
            if type(used_entry[1]) != dict:
                logging.warning(f"Entry is not a dict {used_entry[1]}")
                continue
            logging.debug(f"Increment: {increment}  with entry {used_entry}")
            final_key_list.append(used_entry[0])
            result.append((used_entry[0], {**used_entry[1], "recently_used": True}))
            increment += 1

        for key in self.ranked_keys:
            if key not in self.entries:
                # key not found in entries
                continue

            result.append((key, self.entries[key]))
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
                print(f"Disabled latest entries")
            return

        self.used_entries = self.get_used_entries_from_redis(self.entries)
        # only use the latest 7 entries for the top of the ranking
        self.used_entries = self.used_entries[-7:]

        if self._debug:
            print(f"Used entries: {self.used_entries}")

    def get_used_entries_from_redis(self, entries) -> List[Tuple[str, dict]]:
        """
        returns a list of used entries to be placed on top of the ranking
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
        from python_search.events.latest_used_entries import LatestUsedEntries

        return LatestUsedEntries().get_latest_used_keys()


import datetime

from dateutil import parser


class SearchableEntriesResult:
    """Builds the list of results ready to be consumed by fzf"""

    def __init__(self):
        self._today = datetime.datetime.now()

    @timeit
    def build_entries_result(self, entries: List[Tuple[str, dict]]) -> str:
        """Print results"""
        position = 1
        result = ""
        for name, content in entries:
            try:
                content["key_name"] = name
                content["position"] = position
                content["generated_acronyms"] = generate_acronyms(name)
                content["tags"] = content["tags"] if "tags" in content else []
                if "created_at" in content:
                    date_created = parser.parse(content["created_at"])
                    days_ago = (self._today - date_created).days

                    content["tags"].append(f"created_{days_ago}_days_ago")

                    if days_ago == 0:
                        content["tags"].append(f"today_created")
                    elif days_ago == 1:
                        content["tags"].append(f"yesterday_created")
                    if days_ago < 7:
                        content["tags"].append(f"this_week_created")
                    if days_ago > 7 and days_ago < 14:
                        content["tags"].append(f"previous_week_created")
                    if days_ago < 30:
                        content["tags"].append(f"this_month_created")
                    if days_ago > 30 and days_ago < 60:
                        content["tags"].append(f"previous_month_created")
                    if days_ago < 365:
                        content["tags"].append(f"this_year_created")
                    if days_ago > 365:
                        content["tags"].append(f"previous_year_created")

                content_str = json.dumps(content, default=tuple, ensure_ascii=True)
            except BaseException as e:
                logging.debug(e)
                # print(e)
                # breakpoint()
                content_str = str(content)

            position = position + 1

            content_str = f"{name}:" + content_str
            #  replaces all single quotes for double ones
            #  otherwise the json does not get rendered
            content_str = content_str.replace("'", '"')
            if os.getenv("ENABLE_TIME_IT"):
                # do not print if enable timeit is on
                continue
            result += content_str + "\n"
        return result


if __name__ == "__main__":
    import fire

    fire.Fire()
