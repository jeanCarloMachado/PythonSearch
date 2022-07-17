from typing import Dict, List, Tuple

import numpy as np

from python_search.ranking.entry_embeddings import create_indexed_embeddings
from python_search.ranking.next_item_predictor.training_dataset import \
    TrainingDataset


class Transform:
    """
    Transform pattern
    From training dataset to -> model input
    And from inference dataset -> model input
    """

    # + 1 is for the month number
    # + 1 for entry number
    DIMENSIONS = 2 * 384 + 1 + 1 + 1

    def transform(self, dataset, keep_ids=False) -> Tuple[np.ndarray, np.ndarray]:
        """
        Transform the dataset into X and Y
        Returns a pair with X, Y
        """
        print("Number of rows in the dataset: ", dataset.count())
        print(f"Dimensions of dataset = {Transform.DIMENSIONS}")
        embeddings_keys = self.create_embeddings_training_dataset(dataset)
        X = np.zeros([dataset.count(), Transform.DIMENSIONS])
        Y = np.empty(dataset.count())

        print("X shape:", X.shape)

        collected_keys = dataset.select(*TrainingDataset.columns).collect()

        for i, collected_key in enumerate(collected_keys):
            X[i] = np.concatenate(
                [
                    np.asarray([collected_key.entry_number]),
                    embeddings_keys[collected_key.key],
                    embeddings_keys[collected_key.previous_key],
                    np.asarray([collected_key.month]),
                    np.asarray([collected_key.hour]),
                ]
            )

            Y[i] = collected_key.label

        return X, Y

    def create_embeddings_training_dataset(
        self, dataset: TrainingDataset
    ) -> Dict[str, np.ndarray]:
        """
        create embeddings
        """
        print("Creating embeddings of traning dataset")

        # add embeddings to the dataset
        all_keys = self._get_all_keys_dataset(dataset)

        print("Sample of historical keys: ", all_keys[0:10])

        return create_indexed_embeddings(all_keys)

    def _get_all_keys_dataset(self, dataset: TrainingDataset) -> List[str]:
        collected_keys = dataset.select("key", "previous_key").collect()

        keys = []
        for collected_keys in collected_keys:
            keys.append(collected_keys.key)
            keys.append(collected_keys.previous_key)

        return keys
