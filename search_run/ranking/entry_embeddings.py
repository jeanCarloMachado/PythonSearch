# !/usr/bin/env python
import msgpack_numpy as m
import numpy as np

from search_run.infrastructure.redis import PythonSearchRedis
from search_run.ranking.baseline.train import create_embeddings
from search_run.ranking.entries_loader import EntriesLoader


class EntryEmbeddings:
    def __init__(self):
        self.client = PythonSearchRedis.get_client()

    def sync_to_redis(self):
        """ "
        Write embeddings of keys not present in redis
        """
        embeddings = self.create_for_current_entries()
        for key, embedding in embeddings.items():
            self.write_embedding(key, embedding)

    def test_end_to_end_are_equal(self):
        """
        @todo move this to the tests folder
        """
        embedding = np.zeros((1, 1))
        self.write_embedding("abc", embedding)

        result_embedding = self.read_embedding("abc")
        print(embedding, result_embedding)

        np.testing.assert_array_equal(embedding, result_embedding)

    def write_embedding(self, key: str, embedding: np.ndarray):
        self.client.hset(
            f"k_{key}", "embedding", EmbeddingSerialization.serialize(embedding)
        )

    def read_embedding(self, key):
        return EmbeddingSerialization.read(self.client.hget(key, "embedding"))

    def create_for_current_entries(self):
        """
        Generate embeddings for all currently existing entries
        """
        keys = EntriesLoader.load_all_keys()
        embeddings = create_indexed_embeddings(keys)

        return embeddings


class EmbeddingSerialization:
    @staticmethod
    def read(embedding):
        return m.unpackb(embedding)

    @staticmethod
    def serialize(embedding):
        return m.packb(embedding)


def create_indexed_embeddings(keys):
    unique_keys = list(set(keys))
    embeddings = create_embeddings(unique_keys)
    embeddings_keys = dict(zip(unique_keys, embeddings))
    return embeddings_keys


if __name__ == "__main__":
    import fire

    fire.Fire(EntryEmbeddings)
