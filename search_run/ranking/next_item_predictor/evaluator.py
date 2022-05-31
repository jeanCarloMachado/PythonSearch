import datetime
import logging
import sys

from search_run.config import ConfigurationLoader
from search_run.ranking.entries_loader import EntriesLoader
from search_run.ranking.entry_embeddings import EmbeddingsReader
from search_run.ranking.next_item_predictor.inference import Inference


class Evaluate:
    """
    Central place to evaluate the quality of the model
    """

    def __init__(self):
        self.month = datetime.datetime.now().month
        self.NUM_OF_TOP_RESULTS = 9
        self.NUM_OF_BOTTOM_RESULTS = 4
        logging.basicConfig(
            level=logging.INFO, handlers=[logging.StreamHandler(sys.stdout)]
        )
        from search_run.ranking.models import PythonSearchMLFlow

        self.configuration = ConfigurationLoader().load()
    def evaluate(self, run_id=None):
        """Evaluate a model against our ranking"""
        logging.info("Evaluate model")
        print('Run id ', run_id)
        self.all_latest_keys = EntriesLoader.load_all_keys()
        self.embeddings_keys_latest = EmbeddingsReader().load(self.all_latest_keys)

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
