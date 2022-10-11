from __future__ import annotations

from collections import namedtuple
from typing import List, Optional, Tuple

from python_search.events.latest_used_entries import RecentKeys
from python_search.config import PythonSearchConfiguration
from python_search.feature_toggle import FeatureToggle
from python_search.infrastructure.performance import timeit
from python_search.observability.logger import logging
from python_search.ranking.results import FzfOptimizedSearchResults

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

        self._used_entries: ListOfTupleCreator.type = []

        if self._feature_toggle.is_enabled("ranking_next"):
            from python_search.ranking.next_item_predictor.inference.inference import \
                Inference

            try:
                self._inference = Inference(self._configuration)
            except Exception as e:
                print(f"Could not initialize the inference component. Proceeding without inference, details: {e}")

    @timeit
    def generate(self, print_entries=True, print_weights=False) -> str:
        """
        Recomputes the rank and saves the results on the file to be read
        """

        self._entries: dict = self._configuration.commands
        # by default the rank is just in the order they are persisted in the file
        self._ranked_keys: List[str] = self._entries.keys()

        if self._feature_toggle.is_enabled("ranking_next") and self._inference:
            self._ranked_keys = self._inference.get_ranking(print_weights=print_weights)

        """Populate the variable used_entries  with the results from redis"""
        self._fetch_latest_entries()
        result, only_list = self._merge_and_build_result()

        if not print_entries:
            return

        return self._entries_result.build_entries_result(result)


    def _merge_and_build_result(self) -> List[Tuple[str, dict]]:
        """ "
        Merge the ranking with the latest _entries and make it ready to be printed
        """
        result = []
        increment = 0
        final_key_list = []

        while self._used_entries:
            used_entry = self._used_entries.pop()
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

        for key in self._ranked_keys:
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
        self._used_entries: List[Tuple[str, dict]] = []
        if not self._feature_toggle.is_enabled("ranking_latest_used"):
            return


        self._used_entries: ListOfTupleCreator.type = ListOfTupleCreator().get_list_of_tuples(RecentKeys().get_latest_used_keys(), self._entries)

        # reverse the list given that we pop from the end
        self._used_entries.reverse()
        # only use the latest 7 _entries for the top of the ranking
        self._used_entries = self._used_entries[-self.NUMBER_OF_LATEST_ENTRIES:]


class ListOfTupleCreator:
    type = List[Tuple[str, dict]]

    @staticmethod
    def get_list_of_tuples(from_keys: List[str], entities: dict) -> ListOfTupleCreator.type:
        used_entries = []
        for used_key in from_keys:
            if used_key not in entities:
                continue
            used_entries.append((used_key, entities[used_key]))
        return used_entries

if __name__ == "__main__":
    import fire

    fire.Fire()
