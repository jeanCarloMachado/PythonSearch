import datetime
import logging
from typing import List, Tuple
import sys

import numpy as np

from search_run.ranking.entries_loader import EntriesLoader
from search_run.ranking.entry_embeddings import EmbeddingsReader, EmbeddingSerialization


class Evaluate:
    """
    Central place to evaluate the quality of the model
    """

    def __init__(self):
        self.month = datetime.datetime.now().month
        self.NUM_OF_TOP_RESULTS = 9
        self.NUM_OF_BOTTOM_RESULTS = 4
        logging.basicConfig(level=logging.INFO, handlers=[logging.StreamHandler(sys.stdout)])
        from search_run.ranking.models import PythonSearchMLFlow

        self.model = PythonSearchMLFlow().get_latest_next_predictor_model(debug_info=True)

    def evaluate(self):
        logging.info("Evaluate model")
        self.all_latest_keys = EntriesLoader.load_all_keys()
        self.embeddings_keys_latest = EmbeddingsReader().load(self.all_latest_keys)

        keys_to_test = [
            "my beat81 bookings",
            "set current project as reco",
            "days quality tracking life good day",
        ]

        print({"params_used": {"month": self.month}})

        result = {key: self.get_rank_for_key(key)[0:20] for key in keys_to_test}
        for key in keys_to_test:
            result = self.get_rank_for_key(key)
            print(f"Key: {key}")

            print(f"Top")
            for i in result[0:self.NUM_OF_TOP_RESULTS]:
                print(f"    {i}")

            print(f"Bottom")
            for i in result[-self.NUM_OF_BOTTOM_RESULTS:]:
                print(f"    {i}")

    def get_rank_for_key(self, selected_key) -> List[Tuple[str, float]]:
        """
        Looks what should be next if the current key is the one passed, look for all current existing keys
        """

        X_validation = np.zeros([len(self.all_latest_keys), 2 * 384 + 1])
        X_key = []
        selected_key_embedding = EmbeddingSerialization.read(self.embeddings_keys_latest[selected_key])
        for i, key in enumerate(self.all_latest_keys):
            X_validation[i] = np.concatenate(
                (
                    selected_key_embedding,
                    EmbeddingSerialization.read(self.embeddings_keys_latest[key]),
                    np.asarray([self.month]),
                )
            )
            X_key.append(key)

        X_validation.shape
        Y_pred = self.model.predict(X_validation)
        result = list(zip(X_key, Y_pred))
        result.sort(key=lambda x: x[1], reverse=True)

        return result
