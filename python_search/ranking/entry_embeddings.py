#!/usr/bin/env python3
from typing import List

import msgpack_numpy as m
import numpy as np
from numpy import ndarray

from python_search.infrastructure.performance import timeit
from python_search.infrastructure.redis import PythonSearchRedis
from python_search.ranking.entries_loader import EntriesLoader


class RedisEmbeddingsReader:
    """
    Responsible for quickly reading the embeddings from redis
    """

    def __init__(self):
        self.client = PythonSearchRedis.get_client()

    @timeit
    def load(self, keys) -> dict[str, bytes]:
        """
        Returns a dictionary with the key being the embedding key and the value being the bytes of the value
        """
        pipe = self.client.pipeline()

        for key in keys:
            pipe.hget(f"k_{key}", "embedding")

        all_embeddings = pipe.execute()

        if len(all_embeddings) != len(keys):
            raise Exception(
                "Number of keys returned from redis does not match the number of embeddings found"
            )

        embedding_mapping = dict(zip(keys, all_embeddings))
        return embedding_mapping

    def load_all_keys(self):
        """
        Generate embeddings for all currently existing entries
        """
        keys = EntriesLoader.load_all_keys()

        return self.load(keys)


class RedisEmbeddingsWriter:
    """Responsible for writing the embeddings in redis"""

    def __init__(self):
        self.client = PythonSearchRedis.get_client()

    def sync_missing(self):
        """ "
        Write embeddings of keys not present in redis
        """

        # load current embeddings

        existing_embeddings = RedisEmbeddingsReader().load_all_keys()

        empty_keys = [
            key for key, embedding in existing_embeddings.items() if embedding is None
        ]

        if not len(empty_keys):
            print("No keys missing sync, exit early")
            return

        embeddings = create_indexed_embeddings(empty_keys)

        for key, embedding in embeddings.items():
            self.write_embedding(key, embedding)

        print("Done!")

    def write_embedding(self, key: str, embedding: np.ndarray):
        self.client.hset(
            f"k_{key}", "embedding", EmbeddingSerialization.serialize(embedding)
        )

    def read_embedding(self, key):
        return EmbeddingSerialization.read(self.client.hget(key, "embedding"))

    def create_all(self):
        """
        Generate embeddings for all currently existing entries
        """
        keys = EntriesLoader.load_all_keys()
        embeddings = create_indexed_embeddings(keys)

        for key, embedding in embeddings.items():
            self.write_embedding(key, embedding)

        print("Done!")


class EmbeddingSerialization:
    """Responsible to encode the numpy embeddings in a format readis can read and write from and to"""

    @staticmethod
    def read(embedding):
        return m.unpackb(embedding)

    @staticmethod
    def serialize(embedding):
        return m.packb(embedding)


def create_embeddings(keys: List[str]) -> ndarray:
    from sentence_transformers import SentenceTransformer

    transformer = SentenceTransformer("nreimers/MiniLM-L6-H384-uncased")
    return transformer.encode(keys, batch_size=128, show_progress_bar=True)


def create_indexed_embeddings(keys):
    unique_keys = list(set(keys))
    embeddings = create_embeddings(unique_keys)
    embeddings_keys = dict(zip(unique_keys, embeddings))
    return embeddings_keys


def main():
    import fire

    fire.Fire()


if __name__ == "__main__":
    main()
