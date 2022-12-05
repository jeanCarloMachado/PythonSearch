import logging
import os.path
import sys
from typing import Optional

import pyspark.sql.functions as F
from pyspark.sql import DataFrame, SparkSession
from pyspark.sql.functions import struct, udf
from pyspark.sql.types import FloatType
from pyspark.sql.window import Window

from python_search.events.run_performed.dataset import EntryExecutedDataset
from python_search.infrastructure.performance import timeit
from python_search.search.next_item_predictor.features.times_used import TimesUsed
from python_search.search.next_item_predictor.inference.label import label_formula


class TrainingDataset:
    """
    Builds the dataset ready for training
    """

    FEATURES = (
        "key",
        "previous_key",
        "previous_previous_key",
        "month",
        "hour",
        "entry_number",
        "times_used_previous",
        "times_used_previous_previous",
    )
    COLUMNS = list(FEATURES) + ["label"]

    _DATASET_CACHE_FILE = "/tmp/dataset"

    def __init__(self):
        self._spark = SparkSession.builder.getOrCreate()
        logging.basicConfig(
            level=logging.INFO, handlers=[logging.StreamHandler(sys.stdout)]
        ),
        self._dataframe = None

    @timeit
    def build(self, use_cache=False, only_show=False) -> DataFrame:
        """
        When cache is enabled, writes a parquet in a temporary file
        """
        if use_cache:
            cache = self._read_cache()
            if cache:
                return cache

        dataset_with_aggregations = self._prepare_features()
        dataset = self._add_label_and_cleanup(dataset_with_aggregations)

        logging.info("TrainingDataset ready, writing it to disk")
        self._write_cache(dataset)

        logging.info("Printing a sample of the dataset")
        dataset.show(10)
        if only_show:
            return

        self._dataframe = dataset
        return dataset

    def _prepare_features(self):
        """
         High level feature composition

        Returns:

        """
        search_performed_df = EntryExecutedDataset().load_clean()
        search_performed_df_filtered = self._filter_blacklisted(search_performed_df)
        all_dimensions = self._add_all_features(search_performed_df_filtered)

        base_dataset = self._filter_unused_cols_and_add_autoincrement(all_dimensions)

        features = self._compute_aggregations(all_dimensions, base_dataset)

        return features

    def _add_label_and_cleanup(self, all_features: DataFrame) -> DataFrame:
        """
        Remove all FEATURES which the purpose is to calculate the label
        """

        logging.info("Adding label")

        udf_f = udf(label_formula, FloatType())
        with_label = all_features.withColumn(
            "label", udf_f(struct([all_features[x] for x in all_features.columns]))
        )

        with_label.cache()
        # normalize label
        max_label = (
            with_label.agg({"label": "max"})
            .withColumnRenamed("max(label)", "max_label")
            .collect()[0]
            .max_label
        )
        max_label = float(max_label)
        print(f"Max value for label: {max_label}")

        min_label = (
            with_label.agg({"label": "min"})
            .withColumnRenamed("min(label)", "min_label")
            .collect()[0]
            .min_label
        )
        min_label = float(min_label)
        print(f"Min value for label: {min_label}")

        normalized = with_label.withColumn(
            "label_normalized", (F.col("label") - min_label) / (max_label - min_label)
        )

        print("Replacing the label colum for the normalized version")
        normalized = normalized.withColumnRenamed("label", "label_original")
        result = normalized.withColumnRenamed("label_normalized", "label")

        final_result = result.select(*self.COLUMNS)

        print("Schema of final dataframe")
        final_result.printSchema()

        return final_result

    def _compute_aggregations(self, all_dimensions, base_features) -> DataFrame:
        """
        Adds aggregations of the entries that supports the label formula
        Args:
            all_dimensions:
            base_features:

        Returns:

        """

        # adds performance in the dimension of the triple key,previous key,previous previous key
        grouped3 = (
            all_dimensions.groupBy(
                "month", "hour", "key", "previous_key", "previous_previous_key"
            )
            .agg(F.count("*").alias("times_3"))
            .sort("times_3", ascending=False)
        )
        base_new = base_features.join(
            grouped3,
            on=["month", "hour", "key", "previous_key", "previous_previous_key"],
        )

        # adds performance in the time dimension of the pair key-previous key
        grouped2 = (
            all_dimensions.groupBy("month", "hour", "key", "previous_key")
            .agg(F.count("*").alias("times_2"))
            .sort("times_2", ascending=False)
        )
        base_new = base_new.join(grouped2, on=["month", "hour", "key", "previous_key"])

        # adds global performance of the pair
        global_pair = (
            all_dimensions.groupBy("key", "previous_key")
            .agg(F.count("*").alias("global_pair"))
            .sort("global_pair", ascending=False)
        )

        base_new = base_new.join(global_pair, on=["key", "previous_key"])

        return base_new

    def _filter_unused_cols_and_add_autoincrement(self, all_dimensions) -> DataFrame:
        """
        This is the base dataset that will be send to train
        but before we will add some aggregations to it so we can generate the desired label
        Args:
            all_dimensions:

        Returns:

        """
        base_features = all_dimensions.select(
            "month",
            "hour",
            "key",
            "previous_key",
            "previous_previous_key",
            "times_used_previous",
            "times_used_previous_previous",
        ).distinct()

        window = Window.orderBy(F.col("key"))

        # @todo verify if this number is correct auto-incremented and unique
        base_features = base_features.withColumn(
            "entry_number", F.row_number().over(window)
        )

        print("Base feature")
        base_features.show()

        return base_features

    def _load_searches_performed(self) -> DataFrame:
        return EntryExecutedDataset().load_clean()

    def _add_all_features(self, df: DataFrame) -> DataFrame:
        """
        Return a dataframe with the hole features it will need but not aggregated
        """
        logging.info("Loading searches performed")
        df_with_previous = self._join_with_previous(df)
        print("Add date dimensions")
        with_month = df_with_previous.withColumn("month", F.month("timestamp"))
        with_hour = with_month.withColumn("hour", F.hour("timestamp"))

        times_used = TimesUsed().get_dataframe()
        times_used = times_used.withColumnRenamed("key", "times_used_key")
        times_used = times_used.withColumnRenamed("times_used", "times_used_previous")

        # add previous times used
        features = with_hour.join(
            times_used, times_used.times_used_key == with_hour.previous_key, "left"
        )
        features = features.withColumnRenamed("times_used", "times_used_previous")

        times_used = times_used.withColumnRenamed(
            "times_used_previous", "times_used_previous_previous"
        )
        times_used = times_used.withColumnRenamed(
            "times_used_key", "times_used_previous_key"
        )

        # add previous previous times used
        features = features.join(
            times_used,
            times_used.times_used_previous_key == features.previous_previous_key,
            "left",
        )

        # keep only the necessary columns
        return features.select(
            "month",
            "hour",
            "key",
            "previous_key",
            "previous_previous_key",
            "timestamp",
            "times_used_previous",
            "times_used_previous_previous",
        )

    def _filter_blacklisted(self, df) -> DataFrame:
        # filter out too common keys
        EXCLUDED_ENTRIES = [
            "startsearchrunsearch",
            "search run search focus or open",
            "",
        ]
        return df.filter(~F.col("key").isin(EXCLUDED_ENTRIES))

    @timeit
    def _join_with_previous(self, df):
        """
        Adds the previou_key as an entry
        """
        # build pair dataset with label
        # add literal column
        search_performed_df_tmpcol = df.withColumn("tmp", F.lit("toremove"))
        window = Window.partitionBy("tmp").orderBy("timestamp")

        # add row number to the dataset
        search_performed_df_row_number = search_performed_df_tmpcol.withColumn(
            "row_number", F.row_number().over(window)
        ).sort("timestamp", ascending=False)

        # add previous key to the dataset
        search_performed_df_with_previous = search_performed_df_row_number.withColumn(
            "previous_key", F.lag("key", 1, None).over(window)
        )
        search_performed_df_with_previous_previous = (
            search_performed_df_with_previous.withColumn(
                "previous_previous_key", F.lag("key", 2, None).over(window)
            )
        )

        result = search_performed_df_with_previous_previous.sort(
            "timestamp", ascending=False
        )
        logging.debug("Showing it merged with 2 previous keys", result.show(10))

        return result

    def _write_cache(self, dataset) -> None:
        print("Writing cache dataset to disk")
        if os.path.exists(TrainingDataset._DATASET_CACHE_FILE):
            import shutil

            shutil.rmtree(TrainingDataset._DATASET_CACHE_FILE)

        dataset.write.parquet(TrainingDataset._DATASET_CACHE_FILE)

    def _read_cache(self) -> Optional[DataFrame]:
        if os.path.exists(TrainingDataset._DATASET_CACHE_FILE):
            print("Reading cache dataset")
            return self._spark.read.parquet(TrainingDataset._DATASET_CACHE_FILE)
        else:
            print("Cache does not exist, creating dataset")


if __name__ == "__main__":
    import fire

    fire.Fire(TrainingDataset)
