#!/usr/bin/env python

import os
from typing import List, Literal, Optional

import numpy as np
from pyspark.sql import SparkSession
from sklearn.model_selection import train_test_split

from python_search.configuration.loader import ConfigurationLoader
from python_search.events.run_performed.clean import RunPerformedCleaning
from python_search.next_item_predictor.mlflow_logger import configure_mlflow
from python_search.next_item_predictor.offline_evaluation import (
    OfflineEvaluation,
)
from python_search.next_item_predictor.train_xgboost import TrainXGBoost


class NextItemPredictorPipeline:
    """
    Exposes the whole ML pipeline, the runs everything
    """

    model_types: Literal["xgboost", "keras"] = "xgboost"

    def __init__(self):
        self._fix_python_interpreter_pyspark()
        configuration = ConfigurationLoader().load_config()
        self._model = configuration.get_next_item_predictor_model()
        self._offline_evaluation = OfflineEvaluation()

    def run(
        self,
        train_only: Optional[List[model_types]] = ["xgboost"],
        use_cache=False,
        clean_events_first=False,
        skip_offline_evaluation=False,
        only_print_dataset=False,
    ):
        """
        Trains both xgboost and keras models

        Args:
            train_only:
            use_cache:
            clean_events_first:

        Returns:

        """
        print("Starting pipeline, use --help for understaning the options")

        print("Using cache is:", use_cache)

        if not train_only:
            train_only = ["xgboost", "keras"]
            print("Training all models")
        else:
            print("Training only: ", train_only)

        if clean_events_first:
            RunPerformedCleaning().clean()

        dataset = self._model.load_or_build_dataset()
        if only_print_dataset:
            print(dataset.show())
            return

        X, Y = self._model.transform_collection(dataset)
        X_train, X_test, Y_train, Y_test = train_test_split(
            X, Y, test_size=0.7, random_state=42
        )

        X_test_dataset = self._offline_evaluation.get_X_test_split_of_dataset(
            dataset, X_test
        )

        def delete_ids_colunn(df):
            return np.delete(df, 0, axis=1)

        # delete row number from X_test
        X_test = delete_ids_colunn(X_test)
        X_train = delete_ids_colunn(X_train)

        if "xgboost" in train_only:
            mlflow = configure_mlflow()
            with mlflow.start_run() as active_run:
                print(f"Starting xgboost training, run_id {active_run.info.run_id}")
                model = TrainXGBoost().train(X_train, X_test, Y_train, Y_test)
                mlflow.xgboost.log_model(model, "model")
                if not skip_offline_evaluation:
                    offline_evaluation = self._offline_evaluation.run(
                        model, X_test_dataset
                    )
                    mlflow.log_params(offline_evaluation)

        if "keras" in train_only:
            mlflow = configure_mlflow()
            with mlflow.start_run() as active_run:
                print(f"Starting keras training, run_id {active_run.info.run_id}")
                from python_search.next_item_predictor.train_keras import (
                    TrainKeras,
                )

                model = TrainKeras().train(X_train, X_test, Y_train, Y_test)
                mlflow.keras.log_model(model, "model", keras_module="keras")
                if not skip_offline_evaluation:
                    offline_evaluation = self._offline_evaluation.run(
                        model, X_test_dataset
                    )
                    mlflow.log_params(offline_evaluation)

    def _spark(self):
        return SparkSession.builder.getOrCreate()

    def _fix_python_interpreter_pyspark(self):
        print("Overriding pyspark python executable")

        from subprocess import PIPE, Popen

        command = "whereis python"
        with Popen(command, stdout=PIPE, stderr=None, shell=True) as process:
            output = process.communicate()[0].decode("utf-8")
        print(f"Where is ouptut: {output}")
        # get only the path and remove new line in the end
        path = output.split(" ")[1].split("\n")[0]
        print(f"Using the following path: {path}")
        os.environ["PYSPARK_PYTHON"] = path
        os.environ["PYSPARK_DRIVER_PYTHON"] = path


def main():
    import fire

    fire.Fire(NextItemPredictorPipeline)


if __name__ == "__main__":
    main()
