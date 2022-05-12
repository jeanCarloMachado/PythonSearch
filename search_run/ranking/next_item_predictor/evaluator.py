import datetime
import logging
from typing import List, Tuple

import numpy as np

from search_run.ranking.entries_loader import EntriesLoader
from search_run.ranking.entry_embeddings import EntryEmbeddings


class Evaluate:
    """
    Central place to evaluate the quality of the model
    """

    def evaluate(self, model):
        self.model = model
        logging.info("Evaluate model")
        self.all_latest_keys = EntriesLoader.load_all_keys()
        self.embeddings_keys_latest = EntryEmbeddings().create_for_current_entries()
        keys_to_test = [
            "my beat81 bookings",
            "set current project as reco",
            "days quality tracking life good day",
        ]

        result = {key: self.get_rank_for_key(key)[0:20] for key in keys_to_test}
        for key in keys_to_test:
            result = self.get_rank_for_key(key)
            print(f"Key: {key}")

            print(f"Top")
            for i in result[0:10]:
                print(f"    {i}")

            print(f"Bottom")
            for i in result[-5:]:
                print(f"    {i}")

    def get_rank_for_key(self, selected_key) -> List[Tuple[str, float]]:
        """
        Looks what should be next if the current key is the one passed, look for all current existing keys
        """
        week_number = datetime.datetime.today().isocalendar()[2]

        X_validation = np.zeros([len(self.all_latest_keys), 2 * 384 + 1])
        X_key = []
        for i, key in enumerate(self.all_latest_keys):
            X_validation[i] = np.concatenate(
                (
                    self.embeddings_keys_latest[selected_key],
                    self.embeddings_keys_latest[key],
                    np.asarray([week_number]),
                )
            )
            X_key.append(key)

        X_validation.shape
        Y_pred = self.model.predict(X_validation)
        result = list(zip(X_key, Y_pred))
        result.sort(key=lambda x: x[1], reverse=True)

        return result
