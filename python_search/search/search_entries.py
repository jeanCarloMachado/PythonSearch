from __future__ import annotations

from collections import namedtuple
from typing import List, Literal, Optional, Tuple

from python_search.configuration.configuration import PythonSearchConfiguration
from python_search.events.latest_used_entries import RecentKeys
from python_search.events.ranking_generated import (
    RankingGenerated,
    RankingGeneratedEventWriter,
)
from python_search.logger import setup_inference_logger
from python_search.search.ranked_entries import RankedEntries
from python_search.search.fzf_results_formatter import FzfOptimizedSearchResultsBuilder

ModelInfo = namedtuple("ModelInfo", "features label")


class Search:
    """
    Generates the search for python search
    """

    NUMBER_OF_LATEST_ENTRIES = 30

    _model_info = ModelInfo(["position", "key_lenght"], "input_lenght")
    _next_item_reranker = None
    _latest_entries = None

    def __init__(self, configuration: Optional[PythonSearchConfiguration] = None):
        self.logger = setup_inference_logger()
        if configuration is None:
            configuration = self._load_configuration()

        self._configuration = configuration
        self._ranked_keys: List[str]

        self._entries_result = FzfOptimizedSearchResultsBuilder()
        self._entries: Optional[dict] = None
        self._ranking_generator_writer = RankingGeneratedEventWriter()
        self._ranking_method_used: Literal["BaselineRank"] = "BaselineRank"

        self._recent_keys = RecentKeys()

        if self._configuration.is_rerank_via_model_enabled():
            try:
                from python_search.ps_llm.t5.t5_ranker import (
                    NextItemReranker,
                )

                self._next_item_reranker = NextItemReranker()
            except Exception as e:
                print("Failed to load next item reranker" + str(e))
                self.logger.error("Failed to load next item reranker")
                self.logger.error(e)
                self._next_item_reranker = None

    def search(
        self,
        skip_model=False,
        ignore_recent=False,
        reload_enabled=False,
        fast_mode=False,
    ) -> str:
        """
        Recomputes the rank and saves the results on the file to be read

        skip_model: if you want to use the base rank and the recent features but not the next item model
        reload_enabled: if you are reloading entries (will trigger new embeddings to be computed as well)
        fast_mode: Fast mmode will not use the ranking
        """

        self.logger.debug("Starting search function")
        self._entries: dict = self._configuration.commands
        # by default the rank is just in the order they are persisted in the file
        self._ranked_keys: List[str] = list(self._entries.keys())
        self.latest_entries = self._fetch_latest_used_entries()

        if reload_enabled:
            self.logger.debug("Skipping model due to reload")
            skip_model = True
            ignore_recent = True

            import subprocess

            subprocess.Popen("llm_cli t5_embeddings save_missing_keys", shell=True)
            self.logger.debug("Triggered embeddings to be recomputed")

        if fast_mode:
            self.logger.debug("Skipping model and recent due to fast mode")
            skip_model = True
            ignore_recent = True

        if not skip_model and (self._configuration.is_rerank_via_model_enabled()):
            self.logger.debug("Trying to rerank")
            self._try_torerank_via_model()

        """
        Populate the variable used_entries  with the results from redis
        """
        result = self._merge_result(ignore_recent)

        ranking_generated = self.send_ranking_generated_event(result)
        result_str = self._entries_result.build_entries_result(
            entries=result,
            ranking_uuid=ranking_generated.uuid,
        )

        return result_str

    def send_ranking_generated_event(self, result):
        ranking_generated = RankingGenerated(ranking=[i[0] for i in result[0:100]])
        self._ranking_generator_writer.write(ranking_generated)

        return ranking_generated

    def _try_torerank_via_model(self):
        if not self._next_item_reranker:
            """Reranker not active skipping"""
            return

        try:
            self._ranked_keys = self._next_item_reranker.rank_entries(
                keys=self._ranked_keys, recent_history=self.latest_entries
            )
            self._ranking_method_used = "LLMRankingNextModel"
        except Exception as e:
            print(f"Failed to perform inference, reason {e}")

    def _merge_result(self, ignore_recent) -> RankedEntries.type:
        """
        Merge the search with the latest entries
        """

        if ignore_recent:
            result = []
        else:
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

    def _latest_keys(self) -> List[Tuple[str, dict]]:
        """
        This method retrieves and updates the latest entries in '_entries'.
        Each updated entry gets a "RecentlyUsed" tag. Non-dictionary entries are skipped with a warning.
        The key is removed from '_ranked_keys' if present.
        The function returns a list of tuples, each containing an updated entry's key and content.
        """
        result = []

        if self.latest_entries:
            for key in self.latest_entries:
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

    def _fetch_latest_used_entries(self):
        return self._recent_keys.get_latest_used_keys(self.NUMBER_OF_LATEST_ENTRIES)

    def _load_configuration(self):
        self.logger.debug("Configuration not initialized, loading from file")
        from python_search.configuration.loader import ConfigurationLoader

        configuration = ConfigurationLoader().get_config_instance()
        self.logger.debug("Configuration loaded")
        return configuration


def main():
    import fire

    fire.Fire(Search().search)


if __name__ == "__main__":
    main()
