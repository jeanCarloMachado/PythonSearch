#!/usr/bin/env python
# using ipython interferes with fire arguments passing

import os
from typing import List, Literal, Optional

import numpy as np
from pyspark.sql import DataFrame, SparkSession
from sklearn.model_selection import train_test_split

from python_search.events.run_performed.clean import RunPerformedCleaning
from python_search.search.next_item_predictor.mlflow_logger import configure_mlflow
from python_search.search.next_item_predictor.offline_evaluation import (
    OfflineEvaluation,
)
from python_search.search.next_item_predictor.train_xgboost import TrainXGBoost
from python_search.search.next_item_predictor.training_dataset import TrainingDataset


class NextItemPredictorPipeline:
    """
    Exposes the whole ML pipeline, the runs everything
    """

    model_types: Literal["xgboost", "keras"] = "xgboost"

    def __init__(self):
        os.environ["TIME_IT"] = "1"

    def run(
        self,
        train_only: Optional[List[model_types]] = None,
        use_cache=False,
        clean_first=True,
        skip_offline_evaluation=False,
    ):
        """
        Trains both xgboost and keras models

        Args:
            train_only:
            use_cache:
            clean_first:

        Returns:

        """

        print("Using cache is:", use_cache)

        if not train_only:
            train_only = ["xgboost", "keras"]
        else:
            print("Training only: ", train_only)

        if clean_first:
            RunPerformedCleaning().clean()

        dataset: DataFrame = TrainingDataset().build(use_cache)
        from python_search.search.next_item_predictor.transform import ModelTransform

        X, Y = ModelTransform().transform_collection(dataset, use_cache=use_cache)
        from python_search.search.next_item_predictor.train_keras import TrainKeras

        X_train, X_test, Y_train, Y_test = train_test_split(
            X, Y, test_size=TrainKeras.TEST_SPLIT_SIZE, random_state=42
        )

        X_test_p = X_test
        X_test = np.delete(X_test, 0, axis=1)
        X_train = np.delete(X_train, 0, axis=1)

        if "xgboost" in train_only:
            mlflow = configure_mlflow()
            with mlflow.start_run():
                model = TrainXGBoost().train(X_train, X_test, Y_train, Y_test)
                mlflow.xgboost.log_model(model, "model")
                if not skip_offline_evaluation:
                    offline_evaluation = OfflineEvaluation().run(
                        model, dataset, X_test_p
                    )
                    mlflow.log_params(offline_evaluation)

        if "keras" in train_only:
            mlflow = configure_mlflow()
            with mlflow.start_run():
                from python_search.search.next_item_predictor.train_keras import (
                    TrainKeras,
                )

                model = TrainKeras().train(X_train, X_test, Y_train, Y_test)
                mlflow.keras.log_model(model, "model", keras_module="keras")
                if not skip_offline_evaluation:
                    offline_evaluation = OfflineEvaluation().run(
                        model, dataset, X_test_p
                    )
                    mlflow.log_params(offline_evaluation)

    def _spark(self):
        return SparkSession.builder.getOrCreate()


def main():
    import fire

    fire.Fire(NextItemPredictorPipeline)


if __name__ == "__main__":
    main()
