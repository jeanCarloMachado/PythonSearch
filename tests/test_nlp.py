from __future__ import annotations

import logging
import sys

from numpy import ndarray

from search_run.core_entities import InvertedIndex
from search_run.ranking.nlp import (create_embeddings,
                                    create_ranking_for_text_query,
                                    update_inverted_index_with_embeddings)

logging.basicConfig(level=logging.INFO, handlers=[logging.StreamHandler(sys.stdout)])


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
