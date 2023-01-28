from typing import Tuple, Dict

import numpy as np
from pandas import DataFrame
from pyspark.sql import Window
from pyspark.sql.functions import udf, struct
import pyspark.sql.functions as F

from python_search.configuration.loader import ConfigurationLoader
from python_search.next_item_predictor.inference.input import ModelInput
from python_search.next_item_predictor.v2.previous_key_feature import PreviousKey
from python_search.search.models import PythonSearchMLFlow
from python_search.next_item_predictor.features.entry_embeddings import (
    InferenceEmbeddingsLoader,
)
from python_search.next_item_predictor.features.entry_embeddings.entry_embeddings import (
    create_key_indexed_embedding,
)
from python_search.next_item_predictor.model_interface import ModelInterface


def number_of_same_words(key1, key2) -> int:
    count = 0
    for i in key1.split(" "):
        for j in key2.split(" "):
            if i == j:
                count += 1
    return count


def number_of_same_words_from_row(row):
    return number_of_same_words(row["key_performed"], row["key"])


class NextItemModelV2(ModelInterface):
    PRODUCTION_RUN_ID = "bc55a9e7acb64f6aa05b63158bad9dc6"

    DIMENSIONS = 384 + 1 + 384 + 384

    def __init__(self):
        configuration = ConfigurationLoader().load_config()
        self._all_keys = configuration.commands.keys()
        self.inference_embeddings = InferenceEmbeddingsLoader(self._all_keys)

    def build_dataset(self, debug=True) -> DataFrame:

        print("Building dataset v2")

        self._ranking_df = self._get_ranking_entries_dataset()
        print(f"Rank entries total: {self._ranking_df.count()}")

        self._performed_df = self._get_performed_entries_dataset()
        # decrement the position of the performed entries, it starts at 1 there but at the ranking event at 0

        self._ranking_df = self._remove_rankings_without_performed_entries(
            self._ranking_df, self._performed_df
        )

        # remove entries that contain the performed key from ranking_df
        performed_keys = self._performed_df.select(
            F.col("key").alias("performed_key"),
            F.col("uuid").alias("performed_uuid"),
            F.col("position").alias("performed_position"),
        )

        self._ranking_df = self._ranking_df.join(
            performed_keys,
            on=[
                performed_keys.performed_uuid == self._ranking_df.uuid,
                performed_keys.performed_position == self._ranking_df.position,
            ],
            how="left_anti",
        )

        self._ranking_df = self._add_share_words_count_as_ranking_label()

        # add performed entries to ranking_df
        print("Ranking df schema:")
        self._ranking_df.printSchema()
        print("Performed df schema:")
        self._performed_df.printSchema()

        unioned = self._ranking_df.union(self._performed_df)
        unioned = unioned.withColumn("timestamp", F.unix_timestamp("datetime"))

        window = Window.orderBy(F.col("key"))
        unioned = unioned.withColumn("entry_number", F.row_number().over(window))

        # prepare result for returning
        # select only relevant columns
        dataset = unioned.select(
            "entry_number", "key", "uuid", "datetime", "timestamp", "position", "label"
        )
        # sort dataframe in a readable way
        dataset = dataset.sort(
            ["uuid", "timestamp", "position"], ascending=[True, False, True]
        )

        dfp = (
            PreviousKey()
            .get_previous_n(n=2)
            .select("uuid", "previous_1_key", "previous_2_key")
        )
        dataset = dataset.join(dfp, on=dfp.uuid == dataset.uuid, how="left")

        if debug:
            dataset.show(n=10, truncate=False)
        dataset = dataset.withColumnRenamed("previous_1_key", "previous_key")
        dataset = dataset.withColumnRenamed("previous_2_key", "previous_previous_key")

        return dataset

    def _remove_rankings_without_performed_entries(self, ranking_df, performed_df):
        # remove ranks without performed keys in it
        performed_uuids = performed_df.select("uuid").withColumnRenamed(
            "uuid", "performed_uuid"
        )
        ranking_df = performed_uuids.join(
            ranking_df,
            on=performed_uuids.performed_uuid == self._ranking_df.uuid,
            how="left",
        )
        ranking_df = ranking_df.drop("performed_uuid")
        ranking_df = ranking_df.withColumn("position", F.col("position").cast("int"))
        print(f"Ranks entries with executed item: {ranking_df.count()}")
        return ranking_df

    def _add_share_words_count_as_ranking_label(self):
        ## add number of same words as temporary feature to update the label
        performed_key_and_uuid = self._performed_df.select(
            F.col("uuid").alias("uuid_performed"), F.col("key").alias("key_performed")
        )
        same_words_df = performed_key_and_uuid.join(
            self._ranking_df,
            on=performed_key_and_uuid.uuid_performed == self._ranking_df.uuid,
            how="left",
        )
        udf_f = udf(number_of_same_words_from_row)
        same_words_df = same_words_df.withColumn(
            "share_words_count",
            udf_f(struct([same_words_df[x] for x in same_words_df.columns])),
        )
        self._ranking_df = same_words_df.drop("uuid_performed").drop("key_performed")
        # add same words as criteria for label
        return self._ranking_df.withColumn(
            "label", F.when(F.col("share_words_count") > 0, 2).otherwise(F.col("label"))
        )

    def _decrement_entry_position(self, performed_df):
        print("Decrementing performed entries position")
        performed_df = performed_df.withColumn(
            "position", F.col("position").cast("int")
        )
        performed_df = performed_df.withColumn("position", F.col("position") - 1)
        performed_df = performed_df.withColumn(
            "position", F.col("position").cast("String")
        )

        return performed_df

    def _get_ranking_entries_dataset(self) -> DataFrame:
        """
        Returns the ranking generated data in the format of the base dataset
        :return:
        """
        import pyspark.sql.functions as F
        from python_search.events.ranking_generated import RankingGeneratedDataset

        rg = RankingGeneratedDataset().load()
        rg = rg.withColumn("datetime", F.from_unixtime("timestamp"))

        base_entries = rg.select(
            F.posexplode("ranking").alias("position", "entry"), "uuid", "datetime"
        ).select(F.col("entry").alias("key"), "position", "uuid", "datetime")
        # entries form ranking generated by default contain not executed things
        return base_entries.withColumn("label", F.lit(0))

    def _get_performed_entries_dataset(self) -> DataFrame:
        """
        Loads and returns a DataFrame of performed entries from the EntryExecutedDataset
        :return:
        """
        from python_search.events.run_performed.dataset import EntryExecutedDataset
        import pyspark.sql.functions as F

        performed_entries = EntryExecutedDataset().load_clean()
        performed_entries = performed_entries.filter(
            "rank_uuid IS NOT NULL and rank_position IS NOT NULL"
        ).select(
            F.col("key"),
            F.col("rank_position").alias("position"),
            F.col("rank_uuid").alias("uuid"),
            F.col("timestamp").alias("datetime"),
        )
        performed_entries = performed_entries.withColumn("label", F.lit(5))

        performed_entries = performed_entries.withColumn("share_words_count", F.lit(0))
        performed_entries = self._decrement_entry_position(performed_entries)

        return performed_entries

    def transform_collection(self, dataset: DataFrame) -> Tuple[np.ndarray, np.ndarray]:
        """
        Returns X and Y
        :param dataset:
        :return:
        """

        embeddings_keys = self._create_embeddings_training_dataset(dataset)
        # one extra for the row number
        X = np.zeros([dataset.count(), self.DIMENSIONS + 1])
        Y = np.empty(dataset.count())

        collected_rows = dataset.collect()

        for i, row in enumerate(collected_rows):

            X[i] = np.concatenate(
                [
                    # adds entry number so we can index and select the right row afterwards
                    # it gets deleted before training
                    np.asarray([row.entry_number]),
                    embeddings_keys[row.key],
                    np.asarray([row.timestamp]),
                    embeddings_keys[row.previous_key],
                    embeddings_keys[row.previous_previous_key],
                ]
            )

            Y[i] = row.label

        X = np.where(np.isnan(X), 0.5, X)
        Y = np.where(np.isnan(Y), 0.5, Y)

        return X, Y

    def _NormalizeData(self, data):
        """normalize a value between 0 and 1"""
        return (data - np.min(data)) / (np.max(data) - np.min(data))

    def transform_single(self, inference_input: dict) -> np.ndarray:
        """
        Return X
        :param inference_input:
        :return:
        """
        inference_input_obj: ModelInput = inference_input["inference_input"]
        all_keys = inference_input["all_keys"]
        from datetime import datetime

        timestamp = int(datetime.now().timestamp())

        previous_key_embedding = self.inference_embeddings.get_embedding_from_key(
            inference_input_obj.previous_key
        )
        previous_previous_key_embedding = (
            self.inference_embeddings.get_embedding_from_key(
                inference_input_obj.previous_previous_key
            )
        )

        X = np.zeros([len(all_keys), self.DIMENSIONS])
        for i, key in enumerate(all_keys):
            key_embedding = self.inference_embeddings.get_embedding_from_key(key)

            if key_embedding is None:
                print(f"No embeddings for key: '{key}'")
                continue

            X[i] = np.concatenate(
                (
                    key_embedding,
                    np.asarray([timestamp]),
                    previous_key_embedding,
                    previous_previous_key_embedding,
                )
            )

        return X

    def load_mlflow_model(self, run_id=None):
        model = PythonSearchMLFlow().get_next_predictor_model(run_id=run_id)
        return model

    def get_run_id(self):
        return self.PRODUCTION_RUN_ID

    def _create_embeddings_training_dataset(self, dataset) -> Dict[str, np.ndarray]:
        """
        create embeddings with all training keys and keep them in memory
        """
        print("Creating embeddings of training dataset")

        # add embeddings to the dataset
        collected_keys = dataset.select("key").collect()

        all_keys = []
        for i in collected_keys:
            all_keys.append(i.key)

        previous_1_keys = dataset.select("previous_key").collect()
        for i in previous_1_keys:
            all_keys.append(i.previous_key)

        previous_2_keys = dataset.select("previous_previous_key").collect()
        for i in previous_2_keys:
            all_keys.append(i.previous_previous_key)

        return create_key_indexed_embedding(all_keys)
