from typing import Dict, List, Tuple

import numpy as np
from pyspark.sql import DataFrame

from python_search.ranking.entry_embeddings import create_indexed_embeddings
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
    DIMENSIONS = 2 * 384 + 1 + 1

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
                    np.asarray([row.month]),
                    np.asarray([row.hour]),
                ]
            )

            Y[i] = row.label

        return X, Y

    def transform_inference(self):
        pass

    def _create_embeddings_training_dataset(
        self, dataset: TrainingDataset
    ) -> Dict[str, np.ndarray]:
        """
        create embeddings with all training keys and keep them in memory
        """
        print("Creating embeddings of traning dataset")

        # add embeddings to the dataset
        all_keys = self._get_all_keys_dataset(dataset)

        return create_indexed_embeddings(all_keys)

    def _get_all_keys_dataset(self, dataset: TrainingDataset) -> List[str]:
        collected_keys = dataset.select("key", "previous_key").collect()

        keys = []
        for collected_keys in collected_keys:
            keys.append(collected_keys.key)
            keys.append(collected_keys.previous_key)

        return keys
