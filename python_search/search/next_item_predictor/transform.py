import logging
import os
from typing import Dict, List, Tuple

import numpy as np
from pyspark.sql import DataFrame

from python_search.config import ConfigurationLoader
from python_search.search.next_item_predictor.features.entry_embeddings import (
    InferenceEmbeddingsLoader,
)
from python_search.search.next_item_predictor.features.entry_embeddings.entry_embeddings import (
    create_key_indexed_embedding,
)
from python_search.search.next_item_predictor.inference.input import ModelInput
from python_search.search.next_item_predictor.training_dataset import TrainingDataset


class ModelTransform:
    """
    Transform takes an input and make it ready for inference

    From training dataset to -> _model input
    And from inference dataset -> _model input
    """

    _EMBEDDINGS_ENTRIES = 3

    # 2 embeddings of 384 dimensions
    # + 1 is for the month number
    # + 1 for entry number
    # + 1 for global popularity of previous key
    # + 1 for global popularity of previous_previous key
    DIMENSIONS = _EMBEDDINGS_ENTRIES * 384 + 1 + 1 + 1 + 1

    def __init__(self):
        configuration = ConfigurationLoader().load_config()
        self._all_keys = configuration.commands.keys()
        self.inference_embeddings = InferenceEmbeddingsLoader(self._all_keys)

    def transform_single(self, inference_input: ModelInput, all_keys) -> np.ndarray:
        """
        Transform the inference input into something that can be inferred.
        This is an element wise search.
        """

        previous_key_embedding = self.inference_embeddings.get_embedding_from_key(
            inference_input.previous_key
        )
        previous_previous_key_embedding = (
            self.inference_embeddings.get_embedding_from_key(
                inference_input.previous_previous_key
            )
        )

        # create an inference array for all keys
        X = np.zeros([len(self._all_keys), ModelTransform.DIMENSIONS])
        for i, key in enumerate(all_keys):
            key_embedding = self.inference_embeddings.get_embedding_from_key(key)
            if key_embedding is None:
                logging.warning(f"No content for key ({key})")
                continue

            X[i] = np.concatenate(
                (
                    key_embedding,
                    previous_key_embedding,
                    previous_previous_key_embedding,
                    np.asarray([inference_input.month]),
                    np.asarray([inference_input.hour]),
                    np.asarray([inference_input.times_used_previous]),
                    np.asarray([inference_input.times_used_previous_previous]),
                )
            )

        return X

    def transform_collection(
        self, dataset: DataFrame, use_cache=True
    ) -> Tuple[np.ndarray, np.ndarray]:
        """
        Transform the dataset into X and Y
        Returns a pair with X, Y
        """
        print("Number of rows in the dataset: ", dataset.count())
        print(f"Dimensions of dataset = {ModelTransform.DIMENSIONS}")

        if use_cache:
            if not os.path.exists("/tmp/X.npy") or not os.path.exists("/tmp/Y.npy"):
                raise Exception("Cache not found")
            print("Using transformed data from cache")
            X = np.load("/tmp/X.npy", allow_pickle=True)
            Y = np.load("/tmp/Y.npy", allow_pickle=True)

            return X, Y

        embeddings_keys = self._create_embeddings_training_dataset(dataset)
        # one extra for the row number
        X = np.zeros([dataset.count(), ModelTransform.DIMENSIONS + 1])
        Y = np.empty(dataset.count())

        print("X shape:", X.shape)

        # transform the spark dataframe into a python iterable
        collected_rows = dataset.select(*TrainingDataset.COLUMNS).collect()

        for i, row in enumerate(collected_rows):
            X[i] = np.concatenate(
                [
                    # adds entry number so we can index and select the right row afterwards
                    # it gets deleted before training
                    np.asarray([row.entry_number]),
                    embeddings_keys[row.key],
                    embeddings_keys[row.previous_key],
                    embeddings_keys[row.previous_previous_key],
                    np.asarray([row.month]),
                    np.asarray([row.hour]),
                    np.asarray([row.times_used_previous]),
                    np.asarray([row.times_used_previous_previous]),
                ]
            )

            Y[i] = row.label

        X = np.where(np.isnan(X), 0.5, X)
        Y = np.where(np.isnan(Y), 0.5, Y)

        np.save("/tmp/X.npy", X)
        np.save("/tmp/Y.npy", Y)

        return X, Y

    def _create_embeddings_training_dataset(
        self, dataset: TrainingDataset
    ) -> Dict[str, np.ndarray]:
        """
        create embeddings with all training keys and keep them in memory
        """
        print("Creating embeddings of training dataset")

        # add embeddings to the dataset
        all_keys = self._get_all_keys_from_dataset(dataset)

        return create_key_indexed_embedding(all_keys)

    def _get_all_keys_from_dataset(self, dataset: TrainingDataset) -> List[str]:
        collected_keys = dataset.select("key", "previous_key").collect()

        keys = []
        for collected_keys in collected_keys:
            keys.append(collected_keys.key)
            keys.append(collected_keys.previous_key)

        return keys
