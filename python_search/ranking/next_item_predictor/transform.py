import logging
from typing import Dict, List, Tuple

import numpy as np
from pyspark.sql import DataFrame

from python_search.config import ConfigurationLoader
from python_search.ranking.entry_embeddings import create_key_indexed_embedding
from python_search.ranking.next_item_predictor.inference.embeddings_loader import \
    InferenceEmbeddingsLoader
from python_search.ranking.next_item_predictor.inference.input import \
    InferenceInput
from python_search.ranking.next_item_predictor.training_dataset import \
    TrainingDataset


class Transform:
    """
    Transform takes an input and make it ready for inference

    From training dataset to -> model input
    And from inference dataset -> model input
    """

    # 2 embeddings of 384 dimensions
    # + 1 is for the month number
    # + 1 for entry number
    PREVIOUS_PREVIOUS_ENABLED = False
    KEYS = 3 if PREVIOUS_PREVIOUS_ENABLED else 2

    DIMENSIONS = KEYS * 384 + 1 + 1

    def __init__(self):
        configuration = ConfigurationLoader().load_config()
        self._all_keys = configuration.commands.keys()
        self.inference_embeddings = InferenceEmbeddingsLoader(self._all_keys)

    def transform_train(self, dataset: DataFrame) -> Tuple[np.ndarray, np.ndarray]:
        """
        Transform the dataset into X and Y
        Returns a pair with X, Y
        """
        print("Number of rows in the dataset: ", dataset.count())
        print(f"Dimensions of dataset = {Transform.DIMENSIONS}")

        embeddings_keys = self._create_embeddings_training_dataset(dataset)
        # one extra for the row number
        X = np.zeros([dataset.count(), Transform.DIMENSIONS + 1])
        Y = np.empty(dataset.count())

        print("X shape:", X.shape)

        # transform the spark dataframe into a python iterable
        collected_rows = dataset.select(*TrainingDataset.columns).collect()

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
                ]
            )

            Y[i] = row.label

        return X, Y

    def transform_inference(self, inference_input: InferenceInput) -> np.ndarray:
        """
        Transform the inference input into something that can be inferred
        """

        previous_key_embedding = self.inference_embeddings.get_embedding_from_key(
            inference_input.previous_key
        )
        previous_previous_key_embedding = None
        if Transform.PREVIOUS_PREVIOUS_ENABLED:
            previous_previous_key_embedding = (
                self.inference_embeddings.get_embedding_from_key(
                    inference_input.previous_previous_key
                )
            )

        # create an inference array for all keys
        X = np.zeros([len(self._all_keys), Transform.DIMENSIONS])
        for i, key in enumerate(self._all_keys):
            key_embedding = self.inference_embeddings.get_embedding_from_key(key)
            if key_embedding is None:
                logging.warning(f"No content for key ({key})")
                continue

            if Transform.PREVIOUS_PREVIOUS_ENABLED:
                X[i] = np.concatenate(
                    (
                        key_embedding,
                        previous_key_embedding,
                        previous_previous_key_embedding,
                        np.asarray([inference_input.month]),
                        np.asarray([inference_input.hour]),
                    )
                )
            else:
                X[i] = np.concatenate(
                    (
                        key_embedding,
                        previous_key_embedding,
                        np.asarray([inference_input.month]),
                        np.asarray([inference_input.hour]),
                    )
                )

        return X

    def _create_embeddings_training_dataset(
        self, dataset: TrainingDataset
    ) -> Dict[str, np.ndarray]:
        """
        create embeddings with all training keys and keep them in memory
        """
        print("Creating embeddings of traning dataset")

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
