#!/usr/bin/env python
# using ipython interfers with fire arguments passing
import logging
import os
from typing import Optional

from pyspark.sql import SparkSession
from sklearn.metrics import mean_absolute_error

from python_search.infrastructure.performance import timeit
from python_search.observability.logger import initialize_logging
from python_search.ranking.next_item_predictor.evaluator import Evaluate
from python_search.ranking.next_item_predictor.train_keras import Train
from python_search.ranking.next_item_predictor.train_xgboost import \
    TrainXGBoost
from python_search.ranking.next_item_predictor.training_dataset import \
    TrainingDataset

initialize_logging()


class Pipeline:
    """
    Exposes the whole ML pipeline, the runs everything
    """

    def __init__(self):
        os.environ["TIME_IT"] = "1"

    @timeit
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
            model, _ = self.train_keras(dataset)

        Evaluate().evaluate(model)

    @timeit
    def build_dataset(self, use_cache=False, view_only=False):
        """
        Builds the dataset ready for training
        """
        dataset = TrainingDataset().build(use_cache)

        print("Training dataset is ready, printing top 10", dataset.show(n=10))

        if view_only:
            print("View only enabled will early return")
            return

        return dataset

    @timeit
    def train_keras(
        self,
        *,
        dataset: Optional[TrainingDataset] = None,
        epochs=None,
        use_cache=True,
        log_model=True,
    ):
        if not dataset:
            print(f"Using data with cache: {use_cache} type: {type(use_cache)}")
            dataset = self.build_dataset(use_cache=use_cache)

        print(f"Custom epochs {epochs}")

        if log_model:
            model, metrics, offline_evaluation = Train(epochs).train_and_log(dataset)
        else:
            model, metrics, offline_evaluation = Train(epochs).train(
                dataset, plot_history=True
            )

        print(
            {
                "metrics": metrics,
                "offline_evaluation": offline_evaluation,
            }
        )

    def train(self, use_cache=False, log_model=True):
        parameters = locals()
        del parameters["self"]

        self.train_keras(**parameters)
        self.train_xgboost(**parameters)

    def train_xgboost(self, use_cache=False, log_model=True):
        """
        Train the XGBoost model
        """
        dataset = self.build_dataset(use_cache=use_cache)
        if log_model:
            TrainXGBoost().train_and_log(dataset)
        else:
            TrainXGBoost().train(dataset)

    def evaluate(self):
        """
        Evaluate the latest dataset
        """
        return Evaluate().evaluate

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
        return {
            "baseline_mse": mean_squared_error(pd_naive.label, pd_naive.baseline),
            "baseline_mae": mean_absolute_error(pd_naive.label, pd_naive.baseline),
        }

    def _spark(self):
        return SparkSession.builder.getOrCreate()


def main():
    import fire

    fire.Fire(Pipeline)


if __name__ == "__main__":
    main()
