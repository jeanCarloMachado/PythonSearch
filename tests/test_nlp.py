from __future__ import annotations

import logging
import sys
from typing import List

from numpy import ndarray
from sentence_transformers import SentenceTransformer

logging.basicConfig(level=logging.INFO, handlers=[logging.StreamHandler(sys.stdout)])


class Entry:
    name: str
    value: dict
    embedding: ndarray

    def __init__(self, *, name: str, value: dict, embedding=None):
        self.name = name
        self.value = value
        self.embedding = embedding


class Ranking:
    """Base class that stores entries ranked"""

    entries: List[str]


class InvertedIndex:
    """
    The entity that gets persisted to disk
    """

    ranked_entries: List[Entry]

    @staticmethod
    def from_entries_dict(dict: dict) -> InvertedIndex:
        instance = InvertedIndex()
        instance.ranked_entries = []
        for key, value in dict.items():
            instance.ranked_entries.append(Entry(name=key, value=value))

        return instance

    def store(self):
        pass

    def get_ranking(self) -> Ranking:
        pass


def create_embeddings(entries: List[str]) -> ndarray:
    model = SentenceTransformer("bert-base-nli-mean-tokens")
    text_embeddings = model.encode(entries, batch_size=8)
    logging.debug(f"Embeddings: {text_embeddings}")

    return text_embeddings


def create_ranking_for_text_query(text: str, index: InvertedIndex):
    pass


def test_create_inverted_index_from_dict():
    entries = {
        "abc": {"snippet": "abc"},
        "def": {"snippet": "def"},
    }
    index = InvertedIndex.from_entries_dict(entries)
    assert index.ranked_entries[0].name == "abc"
    assert index.ranked_entries[1].name == "def"


def atest_end_to_end_inverted_index_logic():
    """
    from a set of documents and a queyr
    create their embeddings and rerank the entries based on their similarity
    """
    entries = {
        "abc": {"snippet": "abc"},
        "def": {"snippet": "def"},
    }
    index = InvertedIndex.from_entries_dict(entries)

    result = create_ranking_for_text_query("abc 123", index)
    assert result[0] == "abc"
    assert result[1] == "def"


def atest_embedding():
    result = create_embeddings(["abc"])
    assert result != None
