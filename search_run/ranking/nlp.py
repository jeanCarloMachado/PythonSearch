from __future__ import annotations

import logging
from typing import List

from numpy import ndarray
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity

from search_run.core_entities import InvertedIndex, Ranking


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
