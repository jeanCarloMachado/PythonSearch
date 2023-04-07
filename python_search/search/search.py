from __future__ import annotations

from collections import namedtuple
from typing import List, Literal, Optional

from python_search.configuration.configuration import PythonSearchConfiguration
from python_search.events.latest_used_entries import RecentKeys
from python_search.events.ranking_generated import (
    RankingGenerated,
    RankingGeneratedEventWriter,
)
from python_search.infrastructure.performance import timeit
from python_search.logger import setup_inference_logger
from python_search.search.ranked_entries import RankedEntries
from python_search.search.results import FzfOptimizedSearchResultsBuilder

ModelInfo = namedtuple("ModelInfo", "features label")


class Search:
    """
    Generates the search for python search
    """

    NUMBER_OF_LATEST_ENTRIES = 7

    _model_info = ModelInfo(["position", "key_lenght"], "input_lenght")
    _inference = None

    def __init__(self, configuration: Optional[PythonSearchConfiguration] = None):
        self.logger = setup_inference_logger()
        if configuration is None:
            self.logger.debug('Configuration not initialized, loading from file')
            from python_search.configuration.loader import ConfigurationLoader
            configuration = ConfigurationLoader().get_config_instance()
            self.logger.debug('Configuration loaded')

        self._configuration = configuration
        self._model = None
        self._entries_result = FzfOptimizedSearchResultsBuilder()
        self._entries: Optional[dict] = None
        self._ranking_generator_writer = RankingGeneratedEventWriter()
        self._ranking_method_used: Literal[
            "RankingNextModel", "BaselineRank"
        ] = "BaselineRank"

        if configuration.rerank_via_model:
            self.logger.debug("Reranker enabled in configuration")
            from python_search.next_item_predictor.inference.inference import Inference

            try:
                self._inference = Inference(self._configuration)
            except BaseException as e:
                self.logger.error(
                    f"Could not initialize the inference component. Proceeding without inference, details: {e}"
                )
                self._entries_result.degraded_message = f"{e}"
        self._recent_keys = RecentKeys()

    @timeit
    def search(self, skip_model=False, base_rank=False, stop_on_failure=False, inline_print=False) -> str:
        """
        Recomputes the rank and saves the results on the file to be read

        base_rank: if we want to skip the model and any reranking that also happens on top
        """

        self.logger.debug("Starting search function")
        self._entries: dict = self._configuration.commands
        # by default the rank is just in the order they are persisted in the file
        self._ranked_keys: List[str] = list(self._entries.keys())

        if not skip_model and not base_rank and self._configuration.rerank_via_model:
            self.logger.debug("Trying to rerank")
            self._try_torerank_via_model(stop_on_failure=stop_on_failure)

        """
        Populate the variable used_entries  with the results from redis
        """
        # skip latest entries if we want to use only the base rank
        result = self._build_result()

        ranknig_generated_event = RankingGenerated(
            ranking=[i[0] for i in result[0:100]]
        )
        self._ranking_generator_writer.write(ranknig_generated_event)
        result_str = self._entries_result.build_entries_result(
            entries=result, ranking_uuid=ranknig_generated_event.uuid, inline_print=inline_print
        )

        return result_str

    def _try_torerank_via_model(self, stop_on_failure=False):
        if not self._inference:
            return
        try:
            self._ranked_keys = self._inference.get_ranking()
            self._ranking_method_used = "RankingNextModel"
        except Exception as e:
            print(f"Failed to perform inference, reason {e}")
            if stop_on_failure:
                raise e

    def _build_result(self) -> RankedEntries.type:
        """
        Merge the search with the latest entries
        """

        result = self._latest_keys()

        for key in self._ranked_keys:
            if key not in self._entries:
                # key not found in _entries
                continue

            entry = self._entries[key]
            if type(entry) == dict:
                existing_tags = entry.get("tags", [])
                if type(existing_tags) == str:
                    existing_tags = [existing_tags]

                entry["tags"] = existing_tags + [self._ranking_method_used]
            result.append((key, entry))

        # the result is the one to be returned, final_key_list is to be used in the cache
        return result

    def _latest_keys(self):
        result = []

        latest_entries = self._fetch_latest_entries()
        if latest_entries:
            for key in latest_entries:
                if key not in self._entries:
                    # key not found in _entries
                    continue

                content = self._entries[key]

                # sometimes there can be a bug of saving something other than dicts as _entries
                if type(content) != dict:
                    self.logger.warning(f"Entry is not a dict {content}")
                    continue

                content["tags"] = content.get("tags", []) + ["RecentlyUsed"]
                result.append((key, content))
                # delete key
                if key in self._ranked_keys:
                    self._ranked_keys.remove(key)
        return result

    def _fetch_latest_entries(self):
        """Populate the variable used_entries  with the results from redis"""

        entries = self._recent_keys.get_latest_used_keys()

        # only use the latest 7 entries for the top of the search
        return entries[: self.NUMBER_OF_LATEST_ENTRIES]


def main():
    import fire
    fire.Fire(Search().search)



if __name__ == "__main__":
    main()
