from __future__ import annotations

import datetime
import logging
import os
from typing import List, Optional, Tuple

import numpy as np

from search_run.events.latest_used_entries import LatestUsedEntries
from search_run.infrastructure.performance import timeit
from search_run.ranking.entry_embeddings import EmbeddingSerialization, EmbeddingsReader
from search_run.ranking.models import PythonSearchMLFlow


class Inference:
    """
    Performs the ranking inference
    """

    def __init__(self, configuration, run_id: Optional[str] = None):
        self.configuration = configuration
        self.debug = os.getenv("DEBUG", False)
        if not self.debug:
            self._disable_debug()
        # previous key should be setted in runtime
        self.previous_key = None
        self.all_keys = self.configuration.commands.keys()
        self.model = self._load_mlflow_model(run_id=run_id)
        self.inference_embeddings = InferenceEmbeddingsLoader(self.all_keys)

    @timeit
    def get_ranking(self, predefined_input: Optional[InferenceInput] = None) -> List[str]:
        """
        Gets the ranking from the next item model
        """
        if not predefined_input:
            inference_input = InferenceInput.from_context(self.inference_embeddings)

        X = self._build_dataset(inference_input)
        Y = self._predict(X)

        result = list(zip(self.all_keys, Y))
        result.sort(key=lambda x: x[1], reverse=True)

        only_keys = [entry[0] for entry in result]

        return only_keys

    def _build_dataset(self, inference_input: InferenceInput):

        X = np.zeros([len(self.all_keys), 2 * 384 + 1 + 1])

        previous_key_embedding = self.inference_embeddings.get_embedding_from_key(inference_input.previous_key)

        for i, key in enumerate(self.all_keys):
            embedding = self.inference_embeddings.get_embedding_from_key(key)
            if embedding is None:
                logging.warning(f"No content for key {key}")
                continue

            X[i] = np.concatenate(
                (
                    previous_key_embedding,
                    embedding,
                    np.asarray([inference_input.month]),
                    np.asarray([inference_input.hour]),
                )
            )

        return X

    @timeit
    def _predict(self, X):
        return self.model.predict(X)

    @timeit
    def _load_mlflow_model(self, run_id=None):
        return PythonSearchMLFlow().get_next_predictor_model(run_id=run_id)

    def _disable_debug(self):
        import os

        # disable tensorflow warnings
        os.environ["TF_CPP_MIN_LOG_LEVEL"] = "3"
        # disable system warnings
        import warnings

        warnings.filterwarnings("ignore")
        import logging

        logger = logging.getLogger()
        logger.disabled = True


class InferenceInput:
    hour: int
    month: int
    previous_key: str

    def __init__(self, hour, month, previous_key):
        self.hour = hour
        self.month = month
        self.previous_key = previous_key

    @staticmethod
    def from_context(embedding_loader: InferenceEmbeddingsLoader) -> 'InferenceInput':
        """
        Do inference based on the current time and the recent used keys
        """
        now = datetime.datetime.now()

        instance = InferenceInput(now.hour, now.month, embedding_loader.get_recent_key())

        if os.getenv("DEBUG", False):
            print("Inference input: ", instance.__dict__)

        return instance


class InferenceEmbeddingsLoader:
    def __init__(self, all_keys):
        self.embedding_mapping = EmbeddingsReader().load(all_keys)

    def get_recent_key(self) -> str:
        """Look into the recently used keys and return the most recent for which there are embeddings"""
        for previous_key in LatestUsedEntries().get_latest_used_keys():
            if (
                    previous_key in self.embedding_mapping
                    and self.embedding_mapping[previous_key]
            ):
                return previous_key

        raise Exception('Could not find a recent key with embeddings')

    def get_embedding_from_key(self, key):
        if self.embedding_mapping[key] is None:
            return
        return EmbeddingSerialization.read(self.embedding_mapping[key])
