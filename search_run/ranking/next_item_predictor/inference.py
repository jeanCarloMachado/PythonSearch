from __future__ import annotations

import datetime
import logging
import os
from typing import List, Optional

import numpy as np

from search_run.events.latest_used_entries import LatestUsedEntries
from search_run.infrastructure.performance import timeit
from search_run.ranking.entry_embeddings import EmbeddingSerialization, EmbeddingsReader
from search_run.ranking.models import PythonSearchMLFlow


class Inference:
    """
    Performs the ranking inference
    """

    PRODUCTION_RUN_ID = '92beab211e31400bb98a39a7dce4961d'

    def __init__(self, configuration, run_id: Optional[str] = None):

        self.debug = os.getenv("DEBUG", False)
        self.run_id = run_id if run_id else self.PRODUCTION_RUN_ID

        if self.debug:
            print("Manually setted run id: ", self.run_id)

        self.configuration = configuration
        # previous key should be setted in runtime
        self.previous_key = None
        self.all_keys = self.configuration.commands.keys()
        self.inference_embeddings = InferenceEmbeddingsLoader(self.all_keys)
        self.model = self._load_mlflow_model(run_id=self.run_id)

    @timeit
    def get_ranking(self, predefined_input: Optional[InferenceInput] = None, return_weights=False) -> List[str]:
        """
        Gets the ranking from the next item model
        """
        print('Number of existing keys: ', str(len(self.all_keys)))
        inference_input = predefined_input if predefined_input else InferenceInput.from_context(
            self.inference_embeddings)

        X = self._build_dataset(inference_input)
        Y = self._predict(X)

        result = list(zip(self.all_keys, Y))
        result.sort(key=lambda x: x[1], reverse=True)

        if return_weights:
            return result

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
                    embedding,
                    previous_key_embedding,
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

        model = PythonSearchMLFlow().get_next_predictor_model(run_id=run_id)
        return model
        return model



class InferenceInput:
    hour: int
    month: int
    previous_key: str

    def __init__(self, *, hour, month, previous_key):
        self.hour = hour
        self.month = month
        self.previous_key = previous_key

    @staticmethod
    def from_context(embedding_loader: InferenceEmbeddingsLoader) -> 'InferenceInput':
        """
        Do inference based on the current time and the recent used keys
        """
        now = datetime.datetime.now()

        instance = InferenceInput(hour=now.hour, month=now.month, previous_key=embedding_loader.get_recent_key())

        if os.getenv("DEBUG", False):
            print("Inference input: ", instance.__dict__)

        return instance


class InferenceEmbeddingsLoader:
    def __init__(self, all_keys):
        import copy
        self.all_keys = copy.copy(list(all_keys))
        self.latest_used_entries = LatestUsedEntries()
        self.embedding_mapping = EmbeddingsReader().load(self.all_keys)

    def get_recent_key(self) -> str:
        """Look into the recently used keys and return the most recent for which there are embeddings"""
        iterator = self.latest_used_entries.get_latest_used_keys()
        print("On get_recent_key all keys size: " + str(len(self.all_keys)))
        print("Number of latest used keys: " + str(len(iterator)))

        print("Mapping size: " + str(len(self.embedding_mapping)))
        for previous_key in iterator:
            if previous_key not in self.embedding_mapping:
                print(f"Key {previous_key} not found in mapping")
                continue
            if not self.embedding_mapping[previous_key]:
                print("Key found but no content in: ", previous_key)
                continue

            return previous_key

        print_mapping = False
        extra_message = ''
        if print_mapping:
            extra_message = 'Existing keys: ' + str(self.embedding_mapping.keys())
        raise Exception(f'Could not find a recent key with embeddings' + extra_message)

    def get_embedding_from_key(self, key):
        if self.embedding_mapping[key] is None:
            return
        return EmbeddingSerialization.read(self.embedding_mapping[key])
