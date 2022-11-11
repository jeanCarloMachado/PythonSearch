import datetime
import logging
import sys

from python_search.config import ConfigurationLoader
from python_search.search.entries_loader import EntriesLoader
from python_search.search.next_item_predictor.features.entry_embeddings.entry_embeddings import (
    RedisEmbeddingsReader,
)
from python_search.search.next_item_predictor.inference.inference import Inference


class Evaluate:
    """
    Central place to evaluate the quality of the _model
    """

    def __init__(self):
        self.month = datetime.datetime.now().month
        self.NUM_OF_TOP_RESULTS = 9
        self.NUM_OF_BOTTOM_RESULTS = 4
        logging.basicConfig(
            level=logging.INFO, handlers=[logging.StreamHandler(sys.stdout)]
        )

        self.configuration = ConfigurationLoader().load()

    def evaluate(self, run_id=None):
        """
        Evaluate a _model against our search
        """
        logging.info("Evaluate _model")
        print("Run id ", run_id)
        self.all_latest_keys = EntriesLoader.load_all_keys()
        self.embeddings_keys_latest = RedisEmbeddingsReader().load(self.all_latest_keys)

        keys_to_test = [
            # "my beat81 bookings",
            "set current project as reco",
            "days quality tracking life good day",
        ]

        inference = Inference(configuration=self.configuration, run_id=run_id)

        for key in keys_to_test:
            result = inference.get_ranking(forced_previous_key=key)
            print(f"Key: {key}")

            print(f"Top")
            for i in result[0 : self.NUM_OF_TOP_RESULTS]:
                print(f"    {i}")

            print(f"Bottom")
            for i in result[-self.NUM_OF_BOTTOM_RESULTS :]:
                print(f"    {i}")
