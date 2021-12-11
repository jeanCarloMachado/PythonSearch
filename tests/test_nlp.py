from typing import List

from sentence_transformers import SentenceTransformer


class Rank:
    entries: List[str]


class StoredInvertedIndex:
    """
    The entity that gets persisted to disk
    """

    entries: List[dict]


def create_embedding(entry_str: str):
    model = SentenceTransformer("bert-base-nli-mean-tokens")
    text_embeddings = model.encode([entry_str], batch_size=8)

    return text_embeddings


def test_embedding():
    create_embedding("abc")
