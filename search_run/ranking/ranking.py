from __future__ import annotations

import json
from collections import namedtuple
from typing import List, Tuple

from search_run.acronyms import generate_acronyms
from search_run.base_configuration import PythonSearchConfiguration
from search_run.features import FeatureToggle
from search_run.observability.logger import initialize_systemd_logging, logging


class RankingGenerator:
    """
    Write to the file all the commands and generates shortcuts
    """

    ModelInfo = namedtuple("ModelInfo", "features label")
    model_info = ModelInfo(["position", "key_lenght"], "input_lenght")

    def __init__(self, configuration: PythonSearchConfiguration):
        initialize_systemd_logging()
        self.configuration = configuration
        self.feature_toggle = FeatureToggle()

    def generate(self, recompute_ranking: bool = False):
        """
        Recomputes the rank and saves the results on the file to be read
        """

        entries: dict = self.configuration.commands
        ranked_keys = entries.keys()

        if self.feature_toggle.is_enabled("ranking_b"):
            from search_run.ranking.ml_based import get_ranked_keys

            # if we to recompute the rank we disable the cache
            ranked_keys_b = get_ranked_keys(disable_cache=recompute_ranking)

            missing_from_rank = list(set(ranked_keys) - set(ranked_keys_b))
            ranked_keys = missing_from_rank + ranked_keys_b

        result = []
        used_entries = []

        if self.configuration.supported_features.is_enabled("redis"):
           used_entries = self._get_used_entries_from_redis(entries)

        increment = 1
        for key in ranked_keys:
            increment += 1
            # add used entry on the top on every second iteration
            if increment % 2 == 0 and len(used_entries):
                used_entry = used_entries.pop()
                logging.debug(f"Increment: {increment}  with entry {used_entry}")
                result.append(used_entry)

            if key not in entries:

                #logging.info(f"Key {key} not found in entries")
                continue

            result.append((key, entries[key]))

        return self.print_entries(result)


    def _get_used_entries_from_redis(self, entries):
        """ returns a list of used entries to be placed on top of the ranking """
        used_entries = []
        from search_run.events.latest_used_entries import LatestUsedEntries

        latest_used = LatestUsedEntries().get_latest_used_keys()
        for used_key in latest_used:
            if used_key not in entries or used_key in used_entries:
                continue
            used_entries.append((used_key, entries[used_key]))
            del entries[used_key]
        # reverse the list given that we pop from the end
        used_entries.reverse()

        return used_entries

    def print_entries(self, data: List[Tuple[str, dict]]):
        position = 1
        for name, content in data:
            name_clean = name.lower()
            try:
                content["key_name"] = name_clean
                content["position"] = position
                content["generated_acronyms"] = generate_acronyms(name)
                content_str = json.dumps(content, default=tuple, ensure_ascii=True)
            except BaseException as e:
                logging.debug(e)
                content_str = str(content)

            position = position + 1


            content_str = f"{name_clean}:" + content_str
            #  replaces all single quotes for double ones
            #  otherwise the json does not get rendered
            content_str = content_str.replace("'", '"')
            print(content_str)
