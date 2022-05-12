#!/usr/bin/env python
import logging

from pyspark.sql import SparkSession

from search_run.observability.logger import initialize_logging
from search_run.ranking.models import PythonSearchMLFlow
from search_run.ranking.next_item_predictor.evaluator import Evaluate
from search_run.ranking.next_item_predictor.train import Train
from search_run.ranking.next_item_predictor.training_dataset import TrainingDataset

initialize_logging()


class Pipeline:
    """
    Exposes the whole ML pipeline, the runs everything
    """

    def __init__(self):
        self._spark = SparkSession.builder.getOrCreate()

    def run(self, disable_mlflow=False, use_cached_dataset=True):
        """
        Runs the whole pipeline
        """
        logging.info("End to end ranking")
        dataset = self.build_dataset(use_cache=use_cached_dataset)
        print("MSE baseline: ", self.baseline_mse(dataset))

        if not disable_mlflow:
            model = self.train_and_log(dataset)
        else:
            print("MLFLow disabled")
            model = self.train(dataset)

        Evaluate(model).evaluate()

    def build_dataset(self, use_cache=False):
        """
        Builds the dataset ready for training
        """
        return TrainingDataset().build(use_cache)

    def train_and_log(self, dataset=None):
        """
        Trains the model and logs it to MLFlow
        """

        if not dataset:
            dataset = self.build_dataset(use_cache=True)

        Train().train_and_log(dataset)

    def evaluate_latest(self):
        model = PythonSearchMLFlow().get_latest_next_predictor_model()
        return Evaluate().evaluate(model)


if __name__ == "__main__":
    import fire

    fire.Fire(Pipeline)
