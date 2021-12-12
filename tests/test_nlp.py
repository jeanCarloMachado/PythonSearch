from __future__ import annotations

import logging
import sys
from typing import List, Optional

from numpy import ndarray
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity

logging.basicConfig(level=logging.INFO, handlers=[logging.StreamHandler(sys.stdout)])


class Entry:
    """ Side effect-free """

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


class InvertedIndex:
    """
    The entity that gets persisted to disk
    Side effect-free
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


def update_inverted_index_with_embeddings(
    inverted_index: InvertedIndex,
) -> InvertedIndex:
    """ Add embeddings as properties for the inverted index """

    entries = inverted_index.entries
    embeddings = create_embeddings(
        [entry.serialize() for entry in inverted_index.entries]
    )
    for i, value in enumerate(entries):

        embedding = embeddings[i]
        entries[i].embedding = embedding

    inverted_index.entries = entries

    return inverted_index


def create_embeddings(entries: List[str]) -> ndarray:
    model = SentenceTransformer("bert-base-nli-mean-tokens")
    text_embeddings = model.encode(entries, batch_size=8)
    logging.debug(f"Embeddings: {text_embeddings}")

    return text_embeddings


def create_ranking_for_text_query(query: str, index: InvertedIndex) -> Ranking:
    query_embeeding = create_embeddings([query])[0]

    embeddings_from_documents = [
        entry.embedding for entry in index.entries if entry.has_embedding()
    ]

    if not embeddings_from_documents:
        raise Exception("No embeddings found in any document in the inverted index")

    all_embeddings = [query_embeeding] + embeddings_from_documents
    similarities = cosine_similarity(all_embeddings)

    result = []
    embeddings_index = 1
    for entry in index.entries:
        similarity_score = 0
        if entry.has_embedding():
            similarity_score = similarities[0][embeddings_index]
            embeddings_index = 1 + embeddings_index
        else:
            logging.warning(f"Entry: {entry.name} nas no embedding")

        entry.similarity_score = similarity_score
        result.append(entry)

    entries = sorted(result, key=lambda x: x.get_similarity_score(), reverse=True)
    return Ranking(ranked_entries=entries)


def test_happy_path_end_to_end_inverted_index_logic():
    """
    from a set of documents and a query
    create their embeddings and rerank the entries based on their similarity
    """
    entries = {
        "abc": {"snippet": "abc"},
        "def": {"snippet": "def"},
    }
    index = InvertedIndex.from_entries_dict(entries)
    index = update_inverted_index_with_embeddings(index)

    ranking = create_ranking_for_text_query("abc 123", index)
    assert ranking.entries[0].name == "abc"
    assert ranking.entries[1].name == "def"


def test_update_inverted_index_with_embeddings():
    """
    The function updates the inverted index sucessfully with embeddings
    """
    entries = {
        "abc": {"snippet": "abc"},
        "def": {"snippet": "def"},
    }
    index = InvertedIndex.from_entries_dict(entries)

    assert index.entries[0].embedding is None
    assert index.entries[1].embedding is None

    index = update_inverted_index_with_embeddings(index)

    assert type(index.entries[0].embedding) is ndarray
    assert type(index.entries[1].embedding) is ndarray


def test_create_inverted_index_from_dict():
    """ the inverted index is created from the entries as dictionaries """
    entries = {
        "abc": {"snippet": "abc"},
        "def": {"snippet": "def"},
    }
    index = InvertedIndex.from_entries_dict(entries)
    assert index.entries[0].name == "abc"
    assert index.entries[1].name == "def"


def test_embedding():
    """ test that the create embedding function returns at least something :) """
    result = create_embeddings(["abc"])
    assert type(result[0]) is ndarray
