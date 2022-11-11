#!/usr/bin/env python3
from typing import List, Tuple

import msgpack_numpy as m
import numpy as np
from numpy import ndarray

from python_search.config import ConfigurationLoader
from python_search.infrastructure.performance import timeit
from python_search.infrastructure.redis import PythonSearchRedis
from python_search.search.entries_loader import EntriesLoader


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
        Generate embeddings for all currently existing _entries
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

        embeddings = create_key_indexed_embedding(empty_keys)

        for key, embedding in embeddings.items():
            self.write_embedding(key, embedding)

        print("Done!")

    def sync_all(self):
        """
        Generate embeddings for all currently existing _entries
        """
        keys = EntriesLoader.load_all_keys()
        embeddings = create_key_indexed_embedding(keys)

        for key, embedding in embeddings.items():
            self.write_embedding(key, embedding)

        print("Done!")

    def write_embedding(self, key: str, embedding: np.ndarray):
        self.client.hset(
            f"k_{key}", "embedding", EmbeddingSerialization.serialize(embedding)
        )

    def read_embedding(self, key):
        return EmbeddingSerialization.read(self.client.hget(key, "embedding"))


class EmbeddingSerialization:
    """Responsible to encode the numpy embeddings in a format readis can read and write from and to"""

    @staticmethod
    def read(embedding):
        return m.unpackb(embedding)

    @staticmethod
    def serialize(embedding):
        return m.packb(embedding)


def create_embeddings_from_strings(keys: List[str]) -> ndarray:
    from sentence_transformers import SentenceTransformer

    transformer = SentenceTransformer(
        "nreimers/MiniLM-L6-H384-uncased",
    )
    return transformer.encode(keys, show_progress_bar=True)


def create_key_indexed_embedding(keys) -> dict[str, str]:
    """
    Create an embedding dict
    """
    unique_keys = list(set(keys))

    entries = ConfigurationLoader().load_entries()
    unique_bodies = []

    for key in unique_keys:
        if key in entries:
            body = str(entries[key])
            print(f"For key '{key}', found body to encode: {body}")
            unique_bodies.append(key + " " + body)
        else:
            print(f"Could not find body for key: {key}")
            unique_bodies.append(key)

    embeddings = create_embeddings_from_strings(unique_bodies)
    embeddings_keys = dict(zip(unique_keys, embeddings))
    return embeddings_keys


def main():
    import fire

    fire.Fire()


if __name__ == "__main__":
    main()
