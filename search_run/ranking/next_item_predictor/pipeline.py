#!/usr/bin/env python
# using ipython interfers with fire arguments passing
import logging
from typing import Optional

from pyspark.sql import SparkSession

from search_run.observability.logger import initialize_logging
from search_run.ranking.next_item_predictor.evaluator import Evaluate
from search_run.ranking.next_item_predictor.train import Train
from search_run.ranking.next_item_predictor.training_dataset import TrainingDataset

initialize_logging()


class Pipeline:
    """
    Exposes the whole ML pipeline, the runs everything
    """

    def run(self, disable_mlflow=False, use_cached_dataset=True):
        """
        Runs the whole pipeline
        """
        logging.info("End to end ranking")
        dataset = self.build_dataset(use_cache=use_cached_dataset)

        if not disable_mlflow:
            model, _ = self.train_and_log(dataset)
        else:
            print("MLFLow disabled")
            model, _ = self.train(dataset)

        Evaluate().evaluate(model)

    def build_dataset(self, use_cache=False, view_only=False):
        """
        Builds the dataset ready for training
        """
        dataset = TrainingDataset().build(use_cache)

        print("Training dataset is ready", dataset.sample(0.1).show(n=10))

        if view_only:
            print("View only enabled will early return")
            return

        return dataset

    def train(
        self, *, dataset: Optional[TrainingDataset] = None, epochs=None, use_cache=True
    ):
        if not dataset:
            print(f"Using data with cache: {use_cache} type: {type(use_cache)}")
            dataset = self.build_dataset(use_cache=use_cache)

        print(f"Custom epochs {epochs}")
        model, metrics = Train(epochs).train(dataset, plot_history=True)
        print(metrics)

    def train_and_log(self, dataset=None):
        """
        Trains the model and logs it to MLFlow
        """

        if not dataset:
            dataset = self.build_dataset(use_cache=True)

        return Train().train_and_log(dataset)

    def evaluate(self):
        """
        Evaluate the latest dataset
        """
        return Evaluate().evaluate()

    def baseline_mse(self, dataset=None):
        """
        naive approach of setting the same as input and output, used as baseline to measure the real model against
        """
        import pyspark.sql.functions as F
        from sklearn.metrics import mean_squared_error

        if not dataset:
            dataset = self.build_dataset(use_cache=True)

        # apply only to the  ones with the same name in input and output
        # complete dataset 8k, with the same name in input and output 150
        naive = (
            dataset.filter("key == previous_key")
            .select("key", "label")
            .withColumn("baseline", F.lit(1))
        )
        pd_naive = naive.select("label", "baseline").toPandas()
        return {"baseline_mse": mean_squared_error(pd_naive.label, pd_naive.baseline)}

    def _spark(self):
        return SparkSession.builder.getOrCreate()


if __name__ == "__main__":
    import fire

    fire.Fire(Pipeline)
