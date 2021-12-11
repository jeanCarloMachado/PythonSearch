import unittest

from sentence_transformers import SentenceTransformer


class Rank:
    entries: list[str]


class StoredInvertedIndex:
    """
    The entity that gets persisted to disk
    """

    entries: List[Dict]


def create_embedding(entry_str: str):
    model = SentenceTransformer("bert-base-nli-mean-tokens")
    text_embeddings = model.encode([entry_str], batch_size=8)

    breakpoint()
    return text_embeddings


def test_embedding():

    entry = {}
    result = create_embedding()
