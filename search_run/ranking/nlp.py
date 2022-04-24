from __future__ import annotations

import logging
import pickle
from typing import List

import deprecation
from numpy import ndarray

from search_run.config import config
from search_run.core_entities import InvertedIndex, Ranking
from search_run.ranking.read_projection import ReadProjection


class NlpRanking:
    """
    Entrypoint for cli and other parts of the application to NLP actions
    """

    def __init__(self, configuration):
        self.configuration = configuration

    def compute_embeddings_all_entries(self):
        entries = self.configuration.commands
        inverted_index = InvertedIndex.from_entries_dict(entries)

        embedded_index = update_inverted_index_with_embeddings(inverted_index)
        self._dump_embedded_index(embedded_index)

    def get_read_projection_rank_for_query(self, query):

        logging.getLogger("suds").propagate = False
        logging.config.dictConfig(
            {
                "version": 1,
                "disable_existing_loggers": True,
            }
        )
        logging.disable = True
        inverted_index = self._load_embedded_index()
        result = create_ranking_for_text_query(query, inverted_index)
        return ReadProjection().create(result, extra={"query": query})

    def _dump_embedded_index(self, index: InvertedIndex):
        f = open(config.NLP_PICKLED_EMBEDDINGS, "wb")
        pickle.dump(index, f)
        f.close()

    def _load_embedded_index(self) -> InvertedIndex:
        f = open(config.NLP_PICKLED_EMBEDDINGS, "rb")
        result = pickle.load(f)
        f.close()

        return result


def create_ranking_for_text_query(query: str, index: InvertedIndex) -> Ranking:
    query_embeeding = create_embeddings([query])[0]

    embeddings_from_documents = [
        entry.embedding for entry in index.entries if entry.has_embedding()
    ]

    if not embeddings_from_documents:
        raise Exception("No embeddings found in any document in the inverted index")

    all_embeddings = [query_embeeding] + embeddings_from_documents
    from sklearn.metrics.pairwise import cosine_similarity

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
    """Add embeddings as properties for the inverted index"""

    entries = inverted_index.entries
    embeddings = create_embeddings(
        [entry.serialize() for entry in inverted_index.entries]
    )
    for i, value in enumerate(entries):

        embedding = embeddings[i]
        entries[i].embedding = embedding

    inverted_index.entries = entries

    return inverted_index


@deprecation.deprecated(
    details="Use the  nreimers/MiniLM-L6-H384-uncased embeddings produced in train.py"
)
def create_embeddings(entries: List[str]) -> ndarray:
    logging.info(f"Starting number of keys: {len(entries)}")

    from sentence_transformers import SentenceTransformer

    model = SentenceTransformer("bert-base-nli-mean-tokens")
    text_embeddings = model.encode(entries, batch_size=8)
    logging.debug(f"Embeddings: {text_embeddings}")

    return text_embeddings
