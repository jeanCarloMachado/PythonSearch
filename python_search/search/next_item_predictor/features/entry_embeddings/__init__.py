from __future__ import annotations

import copy

from python_search.events.latest_used_entries import RecentKeys
from python_search.search.next_item_predictor.features.entry_embeddings.entry_embeddings import (
    EmbeddingSerialization,
    RedisEmbeddingsReader,
    RedisEmbeddingsWriter,
)


class InferenceEmbeddingsLoader:
    """
    @Todo, unify embeddings loading for inference but not training
    """

    def __init__(self, all_keys):
        self.all_keys = copy.copy(list(all_keys))
        self.latest_used_entries = RecentKeys()
        self.embedding_mapping = RedisEmbeddingsReader().load(self.all_keys)

    def get_embedding_from_key(self, key: str):
        """
        Return an embedding based on the keys
        """
        if not key in self.embedding_mapping or self.embedding_mapping[key] is None:
            print(
                f"The embedding for ({key}) is empty in redis. Syncing the missing keys"
            )
            RedisEmbeddingsWriter().sync_missing()
            self.embedding_mapping = RedisEmbeddingsReader().load(self.all_keys)

            if self.embedding_mapping[key] is None:
                raise Exception(
                    f"After trying to sync embedding  for key '{key}' is still empty"
                )

        return EmbeddingSerialization.read(self.embedding_mapping[key])

    def get_recent_key_with_embedding(self, second_recent=False) -> str:
        """
        Look into the recently used keys and return the most recent for which there are embeddings
        """
        iterator = self.latest_used_entries.get_latest_used_keys()
        print("On get_recent_key all keys size: " + str(len(self.all_keys)))
        print("Number of latest used keys: " + str(len(iterator)))

        print("Mapping size: " + str(len(self.embedding_mapping)))
        first_found = False
        for previous_key in iterator:
            if previous_key not in self.embedding_mapping:
                print(f"Key {previous_key} not found in mapping")
                continue
            if not self.embedding_mapping[previous_key]:
                print("Key found but no content in: ", previous_key)
                continue

            if second_recent and not first_found:
                first_found = True
                continue

            return previous_key

        print_mapping = False
        extra_message = ""
        if print_mapping:
            extra_message = "Existing keys: " + str(self.embedding_mapping.keys())

        raise Exception(f"Could not find a recent key with embeddings" + extra_message)
