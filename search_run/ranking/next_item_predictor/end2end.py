#!/usr/bin/env python
import logging
import sys

import mlflow
import numpy as np
import pyspark.sql.functions as F
from pyspark.sql.session import SparkSession

from search_run.config import DataConfig
from search_run.observability.logger import initialize_logging
from search_run.ranking.entry_embeddings import create_indexed_embeddings
from search_run.ranking.next_item_predictor.evaluator import Evaluate

initialize_logging()


class EndToEnd:
    """Exposes the whole ML pipeline, the run function does it end-2-end"""

    def run(self):
        logging.info("End to end ranking")
        dataset = self.build_dataset()
        print("MSE baseline: ", self.baseline_mse(dataset))
        dataset.show(n=10)

        model = self.train(dataset)

        Evaluate(model).evaluate()

    def build_dataset(self):
        from search_run.datasets.searchesperformed import SearchesPerformed

        logging.basicConfig(
            level=logging.INFO, handlers=[logging.StreamHandler(sys.stdout)]
        ),

        spark = SparkSession.builder.getOrCreate()
        df = SearchesPerformed(spark).load()

        df.sort("timestamp", ascending=False).show()

        # build pair dataset with label

        import pyspark.sql.functions as F
        from pyspark.sql.window import Window

        # add literal column
        df = df.withColumn("tmp", F.lit("toremove"))
        window = Window.partitionBy("tmp").orderBy("timestamp")

        df = df.withColumn("row_number", F.row_number().over(window)).sort(
            "timestamp", ascending=False
        )
        df = df.withColumn("previous_key", F.lag("key", 1, None).over(window)).sort(
            "timestamp", ascending=False
        )

        pair = df.select("key", "previous_key", "timestamp")

        grouped = (
            pair.groupBy("key", "previous_key")
            .agg(F.count("previous_key").alias("times"))
            .sort("key", "times")
        )
        grouped.cache()
        grouped.count()
        # add the label
        dataset = grouped.withColumn(
            "label", F.col("times") / F.sum("times").over(Window.partitionBy("key"))
        ).orderBy("key")
        dataset = dataset.select("key", "previous_key", "label")
        dataset = dataset.filter("LENGTH(key) > 1")

        return dataset

    def baseline_mse(self, dataset):
        # naive approach of setting the same as input and output, used as baseline to measure the real model against
        from sklearn.metrics import mean_squared_error

        # apply only to the  ones with the same name in input and output
        # complete dataset 8k, with the same name in input and output 150
        naive = (
            dataset.filter("key == previous_key")
            .select("key", "label")
            .withColumn("baseline", F.lit(1))
        )
        pd_naive = naive.select("label", "baseline").toPandas()
        return mean_squared_error(pd_naive.label, pd_naive.baseline)

    def create_embeddings_historical_keys(self, dataset):
        # create embeddings for all historical keys
        from typing import List

        # add embeddings to the dataset

        def all_keys_dataset(dataset) -> List[str]:
            collected_keys = dataset.select("key", "previous_key").collect()

            keys = []
            for collected_keys in collected_keys:
                keys.append(collected_keys.key)
                keys.append(collected_keys.previous_key)

            return keys

        all_keys = all_keys_dataset(dataset)

        return create_indexed_embeddings(all_keys)

    def create_XY(self, dataset):

        embeddings_keys = self.create_embeddings_historical_keys(dataset)

        X = np.zeros([dataset.count(), 2 * 384])
        Y = np.empty(dataset.count())

        X.shape

        collected_keys = dataset.select("key", "previous_key", "label").collect()

        for i, collected_key in enumerate(collected_keys):
            X[i] = np.concatenate(
                [
                    embeddings_keys[collected_key.key],
                    embeddings_keys[collected_key.previous_key],
                ]
            )
            Y[i] = collected_key.label

        return X, Y

    def train(self, dataset):
        mlflow.set_tracking_uri(f"file:{DataConfig.MLFLOW_MODELS_PATH}")
        # this creates a new experiment
        mlflow.set_experiment(DataConfig.NEXT_ITEM_EXPERIMENT_NAME)
        mlflow.autolog()
        # try mlflow.keras.autolog()

        with mlflow.start_run():

            X, Y = self.create_XY(dataset)

            from sklearn.model_selection import train_test_split

            X_train, X_test, Y_train, Y_test = train_test_split(
                X, Y, test_size=0.20, random_state=42
            )

            from keras import layers
            from keras.models import Sequential

            model = Sequential()
            model.add(layers.Dense(32, activation="relu", input_shape=X[1].shape))
            model.add(layers.Dense(1))
            model.compile(optimizer="rmsprop", loss="mse", metrics=["mae"])
            model.fit(X_train, Y_train, epochs=10, batch_size=32)

            train_mse, train_mae = model.evaluate(X_train, Y_train)

            test_mse, test_mae = model.evaluate(X_test, Y_test)

            metrics = {
                "train_mse": train_mse,
                "train_mae": train_mae,
                "test_mse": test_mse,
                "test_mae": test_mae,
            }
            print(metrics)

            mlflow.log_params(metrics)

        return model


if __name__ == "__main__":
    import fire

    fire.Fire(EndToEnd)
