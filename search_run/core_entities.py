"""

Core entities reused in the hole project.
They should be side-effect free

"""
from __future__ import annotations

from enum import Enum
from typing import List, Optional

from numpy import ndarray


class Entry:
    """
    An python dictionary we write in PythonSearch

    """

    name: str
    value: Optional[dict]
    embedding: Optional[ndarray]
    similarity_score: Optional[float]

    def __init__(self, *, name: str, value: dict = None, embedding=None):
        self.name = name
        self.value = value
        self.embedding = embedding

    def has_embedding(self) -> bool:
        return self.embedding is not None

    def get_similarity_score(self) -> float:
        """ returns a score, if none will then return 0"""
        return self.similarity_score if self.similarity_score else 0.0

    def serialize(self) -> str:
        return f"{self.name} {self.value}"


class Ranking:
    entries: List[Entry] = []

    def __init__(self, *, ranked_entries: List[Entry]):
        self.entries = ranked_entries

    def get_only_names(self) -> List[str]:
        return [entry.name for entry in self.entries]


class InvertedIndex:
    """
    The entity that gets persisted to disk
    """

    entries: List[Entry]

    @staticmethod
    def from_entries_dict(dict: dict) -> InvertedIndex:
        instance = InvertedIndex()
        instance.entries = []
        for key, value in dict.items():
            instance.entries.append(Entry(name=key, value=value))

        return instance

    def serialize(self) -> str:
        pass


class RankingAlgorithms(Enum):
    # the order of the dictionary on the page, fastest but not as optimized
    DICT_ORDER = "dict_order"
    # Order by the latest used
    LATEST_USED = "latest_used"

    @staticmethod
    def from_str(string: str) -> "RankingAlgorithms":
        if string == "dict_order":
            return RankingAlgorithms.DICT_ORDER
        elif string == "LATEST_USED":
            return RankingAlgorithms.LATEST_USED

        raise Exception(f"String: {string} does not match any ranking method")
