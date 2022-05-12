from __future__ import annotations

import json
from collections import namedtuple
from typing import List, Tuple

from search_run.acronyms import generate_acronyms
from search_run.config import PythonSearchConfiguration
from search_run.features import FeatureToggle
from search_run.infrastructure.redis import PythonSearchRedis
from search_run.observability.logger import initialize_systemd_logging, logging
from search_run.ranking.baseline.serve import get_ranked_keys


class RankingGenerator:
    """
    Write to the file all the commands and generates shortcuts
    """

    ModelInfo = namedtuple("ModelInfo", "features label")
    model_info = ModelInfo(["position", "key_lenght"], "input_lenght")

    def __init__(self, configuration: PythonSearchConfiguration):
        # initialize_systemd_logging()
        self.configuration = configuration
        self.feature_toggle = FeatureToggle()
        self.is_redis_supported = self.configuration.supported_features.is_enabled(
            "redis"
        )

        if self.is_redis_supported:
            self.redis_client = PythonSearchRedis.get_client()

        self.used_entries: List[Tuple[str, dict]] = []

    def generate_with_caching(self):
        """
        Uses cached rank if available and only add new keys on top
        """
        self.generate(recompute_ranking=False)

    def generate(self, recompute_ranking: bool = True):
        """
        Recomputes the rank and saves the results on the file to be read
        """

        self.entries: dict = self.configuration.commands
        # by default the rank is just in the order they are persisted in the file
        self.ranked_keys: List[str] = self.entries.keys()

        self._build_rank(recompute_ranking)
        result, final_list = self._merge_and_build_result()

        if self.is_redis_supported and recompute_ranking:
            encoded_list = "|".join(final_list)
            # breakpoint()
            self.redis_client.set("cache_ranking_result", encoded_list)

        return self.print_entries(result)

    def _build_rank(self, recompute_ranking):
        """Mutate self.ranked keys with teh results, supports caching"""
        if self.is_redis_supported and not recompute_ranking:
            keys = self.redis_client.get("cache_ranking_result")
            keys = keys.decode("utf-8").split("|")

            missing_keys = set(self.ranked_keys) - set(keys)
            self.ranked_keys = list(missing_keys) + keys

            return

        try:
            if self.feature_toggle.is_enabled("ranking_next"):
                self.ranked_keys = self.get_ranking_next()
            elif self.feature_toggle.is_enabled("ranking_b"):
                self.ranked_keys = self.get_ranking_b(recompute_ranking)
        except BaseException as e:
            logging.info(f"Failed to get the ranking next with error: {e}")

        self._fetch_latest_entries()

    def _merge_and_build_result(self) -> List[Tuple[str, dict]]:
        """ "
        Merge the ranking with teh latest entries and make it ready to be printed
        """
        result = []
        increment = 0
        final_key_list = []
        for key in self.ranked_keys:
            # add used entry on the top on every second iteration
            if increment % 2 == 0 and len(self.used_entries):
                used_entry = self.used_entries.pop()
                logging.debug(f"Increment: {increment}  with entry {used_entry}")
                final_key_list.append(used_entry[0])
                result.append((used_entry[0], {**used_entry[1], "recently_used": True}))
                increment += 1

            if key not in self.entries:
                # key not found in entries
                continue

            result.append((key, self.entries[key]))
            final_key_list.append(key)
            increment += 1

        return result, final_key_list

    def _fetch_latest_entries(self):
        self.used_entries: List[Tuple[str, dict]] = []
        if self.configuration.supported_features.is_enabled(
            "redis"
        ) and self.feature_toggle.is_enabled("ranking_latest_used"):
            self.used_entries = self.get_used_entries_from_redis(self.entries)

    def get_ranking_next(self, debug=False, top_n=-1) -> List[str]:
        """
        Gets the ranking from the next item model
        """

        if not debug:
            import os

            # disable tensorflow warnings
            os.environ["TF_CPP_MIN_LOG_LEVEL"] = "3"
            # disable system warnings
            import warnings

            warnings.filterwarnings("ignore")
            import logging

            logger = logging.getLogger()
            logger.disabled = True

        import numpy as np

        from search_run.events.latest_used_entries import LatestUsedEntries
        from search_run.ranking.entry_embeddings import EmbeddingSerialization
        from search_run.ranking.models import PythonSearchMLFlow

        all_keys = self.configuration.commands.keys()
        previous_key = LatestUsedEntries().get_latest_used_keys()[0]
        if debug:
            print(f"Key Previous: '{previous_key}'")

        client = LatestUsedEntries.get_redis_client()
        pipe = client.pipeline()

        for key in all_keys:
            pipe.hget(f"k_{key}", "embedding")

        all_embeddings = pipe.execute()

        if len(all_embeddings) != len(all_keys):
            raise Exception(
                "Number of keys returned from redis does not match the number of embeddings found"
            )

        embedding_mapping = dict(zip(all_keys, all_embeddings))

        for previous_key in LatestUsedEntries().get_latest_used_keys():
            if previous_key in embedding_mapping and embedding_mapping[previous_key]:
                # exits the loop as soon as we find an existing previous key
                logging.info(f"Picked previous key: {previous_key}")
                break
            else:
                logging.warning(
                    f"Could not find embedding for previous key {previous_key}, value: "
                    f"{embedding_mapping.get(previous_key)}"
                )

        logging.info(f"Previous key: {previous_key}")

        previous_key_embedding = EmbeddingSerialization.read(
            embedding_mapping[previous_key]
        )

        X = np.zeros([len(all_keys), 2 * 384])
        for i, (key, embedding) in enumerate(embedding_mapping.items()):
            if embedding is None:
                logging.warning(f"No content for key {key}")
                continue
            X[i] = np.concatenate(
                (
                    previous_key_embedding,
                    EmbeddingSerialization.read(embedding),
                )
            )

        model = PythonSearchMLFlow().get_latest_next_predictor_model()
        Y = model.predict(X)

        result = list(zip(all_keys, Y))
        result.sort(key=lambda x: x[1], reverse=True)

        if debug:
            # only return the top 20 for debugging
            return result[0:20]

        only_keys = [entry[0] for entry in result]

        if top_n > 0:
            only_keys = only_keys[0:top_n]

        return only_keys

    def get_ranking_b(self, recompute_ranking) -> List[str]:
        from search_run.ranking.baseline.serve import get_ranked_keys

        # if we to recompute the rank we disable the cache
        ranked_keys_b = get_ranked_keys(disable_cache=recompute_ranking)

        missing_from_rank = list(set(self.ranked_keys) - set(ranked_keys_b))
        return missing_from_rank + ranked_keys_b

    def get_used_entries_from_redis(self, entries) -> List[Tuple[str, dict]]:
        """
        returns a list of used entries to be placed on top of the ranking
        """
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


if __name__ == "__main__":
    import fire

    fire.Fire()
