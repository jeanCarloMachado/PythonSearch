from __future__ import annotations

from collections import namedtuple
from typing import List, Optional, Literal

from python_search.config import PythonSearchConfiguration
from python_search.events.latest_used_entries import RecentKeys
from python_search.feature_toggle import FeatureToggle
from python_search.infrastructure.performance import timeit
from python_search.ranking.ranked_entries import RankedEntries
from python_search.ranking.results import FzfOptimizedSearchResults
import logging

ModelInfo = namedtuple("ModelInfo", "features label")


class RankingGenerator:
    """
    Generates the ranking for python search
    """

    NUMBER_OF_LATEST_ENTRIES = 7

    _model_info = ModelInfo(["position", "key_lenght"], "input_lenght")
    _inference = None

    def __init__(self, configuration: Optional[PythonSearchConfiguration] = None):
        self._configuration = configuration
        self._feature_toggle = FeatureToggle()
        self._model = None
        self._entries_result = FzfOptimizedSearchResults()
        self._used_entries: Optional[List[str]] = None
        self._ranking_method_used: Literal['RankingNextModel', 'BaselineRank'] = 'BaselineRank'

        if self._feature_toggle.is_enabled("ranking_next"):
            from python_search.ranking.next_item_predictor.inference.inference import \
                Inference

            try:
                self._inference = Inference(self._configuration)
            except Exception as e:
                print(
                    f"Could not initialize the inference component. Proceeding without inference, details: {e}"
                )

    @timeit
    def generate(self) -> str:
        """
        Recomputes the rank and saves the results on the file to be read
        """

        self._entries: dict = self._configuration.commands
        # by default the rank is just in the order they are persisted in the file
        self._ranked_keys: List[str] = list(self._entries.keys())

        if self._feature_toggle.is_enabled("ranking_next") and self._inference:
            self._rerank_via_model()

        """Populate the variable used_entries  with the results from redis"""
        result = self._merge_with_latest_used()

        return self._entries_result.build_entries_result(result)

    def _rerank_via_model(self):
        try:
            self._ranked_keys = self._inference.get_ranking()
            self._ranking_method_used = 'RankingNextModel'
        except Exception as e:

            print(f"Failed to perform inference, reason {e}")

            # raise e
    def _merge_with_latest_used(self) -> RankedEntries.type:
        """
        Merge the ranking with the latest entries
        """
        self._fetch_latest_entries()

        result = []

        while self._used_entries:
            key = self._used_entries.pop()

            if key not in self._entries:
                # key not found in _entries
                continue

            content = self._entries[key]

            # sometimes there can be a bug of saving something other than dicts as _entries
            if type(content) != dict:
                logging.warning(f"Entryentry_content is not a dict {content}")
                continue


            content['tags'] = content.get('tags', []) + ['RecentlyUsed']
            result.append((key, content))
            # delete key
            self._ranked_keys.remove(key)

        for key in self._ranked_keys:
            if key not in self._entries:
                # key not found in _entries
                continue

            entry = self._entries[key]
            if type(entry) == dict:
                existing_tags = entry.get('tags', [])
                if type(existing_tags) == str:
                    existing_tags = [existing_tags]

                entry['tags'] = existing_tags + [self._ranking_method_used]
            result.append((key, entry))

        # the result is the one to be returned, final_key_list is to be used in the cache
        return result

    def _fetch_latest_entries(self):
        """Populate the variable used_entries  with the results from redis"""
        if not self._feature_toggle.is_enabled("ranking_latest_used"):
            return

        self._used_entries = RecentKeys().get_latest_used_keys()

        # reverse the list given that we pop from the end
        self._used_entries.reverse()
        # only use the latest 7 _entries for the top of the ranking
        self._used_entries = self._used_entries[-self.NUMBER_OF_LATEST_ENTRIES :]


if __name__ == "__main__":
    import fire

    fire.Fire()
