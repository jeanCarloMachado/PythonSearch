#!/usr/bin/env python
# using ipython interferes with fire arguments passing

from typing import Literal, List
import os
from typing import Optional

from pyspark.sql import SparkSession

from python_search.events.run_performed.clean import RunPerformedCleaning
from python_search.infrastructure.performance import timeit
from python_search.ranking.next_item_predictor.train_keras import Train
from python_search.ranking.next_item_predictor.train_xgboost import \
    TrainXGBoost
from python_search.ranking.next_item_predictor.training_dataset import \
    TrainingDataset


class NextItemPredictorPipeline:
    """
    Exposes the whole ML pipeline, the runs everything
    """
    model_types: Literal["xgboost", "keras"] = "xgboost"

    def __init__(self):
        os.environ["TIME_IT"] = "1"

    def run(self, train_only: Optional[List[model_types]] = None, use_cache=True, clean_first=True):
        """
        Trains both xgboost and keras models

        Args:
            use_cache:
            log_model:

        Returns:

        """
        if not train_only:
            train_only = ["xgboost", "keras"]
        else:
            print('Training only: ', train_only)

        if clean_first:
            RunPerformedCleaning().clean()

        dataset = TrainingDataset().build(use_cache)

        if "xgboost" in train_only:
            TrainXGBoost().train_and_log(dataset)
        if "keras" in train_only:
            Train().train_and_log(dataset)

    def _spark(self):
        return SparkSession.builder.getOrCreate()


def main():
    import fire

    fire.Fire(NextItemPredictorPipeline)


if __name__ == "__main__":
    main()
