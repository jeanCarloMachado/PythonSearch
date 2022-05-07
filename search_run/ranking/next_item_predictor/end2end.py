#!/usr/bin/env python
import logging
import sys
from typing import List, Tuple

import numpy as np
import pyspark.sql.functions as F
from pyspark.sql.session import SparkSession

from search_run.observability.logger import initialize_logging
from search_run.ranking.baseline.train import create_embeddings

initialize_logging()


def create_indexed_embeddings(keys):
    unique_keys = list(set(keys))
    embeddings = create_embeddings(unique_keys)
    embeddings_keys = dict(zip(unique_keys, embeddings))
    return embeddings_keys


class EndToEnd:
    """Exposes the whole ML pipeline, the run function does it end-2-end"""

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
        mse, mae = model.evaluate(X_train, Y_train)
        print("train mse and mae: ", mse, mae)
        mse, mae = model.evaluate(X_test, Y_test)
        print("test mse and mae: ", mse, mae)

        return model

    def run(self):
        logging.info("End to end ranking")
        dataset = self.build_dataset()
        print("MSE baseline: ", self.baseline_mse(dataset))
        dataset.show(n=10)

        model = self.train(dataset)

        Evaluate(model).evaluate()


class Evaluate:
    def __init__(self, model):
        self.model = model

    def evaluate(self):
        logging.info("Evaluate model")
        self.all_latest_keys = self.load_all_keys()
        self.embeddings_keys_latest = create_indexed_embeddings(self.all_latest_keys)

        keys_to_test = [
            "my beat81 bookings",
            "set current project as reco",
            "days quality tracking life good day",
        ]

        result = {key: self.get_rank_for_key(key)[0:20] for key in keys_to_test}
        import pandas as pd

        pd.set_option("display.max_rows", None, "display.max_columns", None)

        df = pd.DataFrame.from_dict(result)
        print(df)

    def load_all_keys(self) -> List[str]:
        from entries.main import config

        return list(config.commands.keys())

    def get_rank_for_key(self, selected_key) -> List[Tuple[str, float]]:
        """
        Looks what should be next if the current key is the one passed, look for all current existing keys
        """

        X_validation = np.zeros([len(self.all_latest_keys), 2 * 384])
        X_key = []
        for i, key in enumerate(self.all_latest_keys):
            X_validation[i] = np.concatenate(
                (
                    self.embeddings_keys_latest[selected_key],
                    self.embeddings_keys_latest[key],
                )
            )
            X_key.append(key)

        X_validation.shape
        Y_pred = self.model.predict(X_validation)
        result = list(zip(X_key, Y_pred))
        result.sort(key=lambda x: x[1], reverse=True)

        return result


if __name__ == "__main__":
    import fire

    fire.Fire(EndToEnd)