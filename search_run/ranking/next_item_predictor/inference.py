import datetime
import logging
import os
from typing import List, Optional

import numpy as np

from search_run.events.latest_used_entries import LatestUsedEntries
from search_run.infrastructure.performance import timeit
from search_run.ranking.entry_embeddings import EmbeddingSerialization
from search_run.ranking.models import PythonSearchMLFlow


class Inference:
    """
    Performs the ranking inference
    """

    def __init__(self, configuration, run_id: Optional[str]=None):
        self.configuration = configuration
        self.debug = os.getenv("DEBUG", False)
        self.forced_previous_key = None
        # previous key should be setted in runtime
        self.previous_key = None
        self.all_keys = self.configuration.commands.keys()
        self.model = self._load_mlflow_model(run_id=run_id)

    @timeit
    def get_ranking(self, forced_previous_key: Optional[str] = None) -> List[str]:
        """
        Gets the ranking from the next item model
        """
        self.forced_previous_key = forced_previous_key

        if not self.debug:
            self._disable_debug()

        self._load_all_keys_embeddings()
        previous_key_embedding = self._get_embedding_previous_key()

        X = self._build_dataset(previous_key_embedding)
        self._load_mlflow_model()
        Y = self._predict(X)

        result = list(zip(self.all_keys, Y))
        result.sort(key=lambda x: x[1], reverse=True)

        only_keys = [entry[0] for entry in result]

        return only_keys

    def _build_dataset(self, previous_key_embedding):

        now = datetime.datetime.now()
        month = now.month
        hour = now.hour

        if self.debug:
            print(
                "Inference parameters",
                {"hour": hour, "month": month, "previous_key": self.previous_key},
            )

        X = np.zeros([len(self.all_keys), 2 * 384 + 1 + 1])
        for i, (key, embedding) in enumerate(self.embedding_mapping.items()):
            if embedding is None:
                logging.warning(f"No content for key {key}")
                continue
            X[i] = np.concatenate(
                (
                    previous_key_embedding,
                    EmbeddingSerialization.read(embedding),
                    np.asarray([month]),
                    np.asarray([hour]),
                )
            )
        return X

    @timeit
    def _predict(self, X):
        return self.model.predict(X)

    @timeit
    def _load_mlflow_model(self, run_id=None):
        return PythonSearchMLFlow().get_next_predictor_model(run_id=run_id)

    @timeit
    def _load_all_keys_embeddings(self):
        from search_run.ranking.entry_embeddings import EmbeddingsReader

        self.embedding_mapping = EmbeddingsReader().load(self.all_keys)

    @timeit
    def _get_embedding_previous_key(self):

        if self.forced_previous_key:
            print("Forcing previous key")
            self.previous_key = self.forced_previous_key
        else:
            self.previous_key = self._find_previous_key_with_embedding()

        logging.info(f"Previous key: {self.previous_key}")

        return EmbeddingSerialization.read(self.embedding_mapping[self.previous_key])

    def _find_previous_key_with_embedding(self) -> str:
        """Look into the recently used keys and"""
        for previous_key in LatestUsedEntries().get_latest_used_keys():
            if (
                previous_key in self.embedding_mapping
                and self.embedding_mapping[previous_key]
            ):
                previous_key
                # exits the loop as soon as we find an existing previous key
                if self.debug:
                    print(f"Picked previous key: {previous_key}")
                break
            else:
                logging.warning(
                    f"Could not find embedding for previous key {previous_key}, value: "
                    f"{self.embedding_mapping.get(self.previous_key)}"
                )
        return previous_key

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
