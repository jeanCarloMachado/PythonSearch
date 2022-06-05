import logging
import os.path
import sys
from typing import Optional

from pyspark.sql import DataFrame

import pyspark.sql.functions as F
from pyspark.sql import SparkSession
from pyspark.sql.window import Window

from search_run.datasets.searchesperformed import SearchesPerformed
from search_run.infrastructure.performance import timeit
from search_run.ranking.next_item_predictor.nextitemmodel import NextItemModel


class TrainingDataset:
    """
    Builds the dataset ready for training
    """


    DATASET_CACHE_FILE = "/tmp/dataset"

    def __init__(self):
        self._spark = SparkSession.builder.getOrCreate()
        logging.basicConfig(
            level=logging.INFO, handlers=[logging.StreamHandler(sys.stdout)]
        ),

    @timeit
    def build(self, use_cache=False, write_cache=True) -> DataFrame:
        """
        When cache is enabled, writes a parquet in a temporary file
        """
        if use_cache:
            cache = self._read_cache()
            if cache:
                return cache

        search_performed_df = SearchesPerformed().load()

        # filter out too common keys
        excluded_keys = ["startsearchrunsearch", "search run search focus or open", ""]
        search_performed_df_filtered = search_performed_df.filter(
            ~F.col("key").isin(excluded_keys)
        )
        logging.info("Loading searches performed")

        df_with_previous = self._join_with_previous(search_performed_df_filtered)

        logging.info("Group by month")
        with_month = df_with_previous.withColumn("month", F.month("timestamp"))


        logging.info("Group by day")
        with_hour = with_month.withColumn("day", F.dayofweek("timestamp"))

        # keep only the necessary columns
        columns = NextItemModel.x_columns + ("timestamp",)
        pair = with_hour.select(*columns)

        logging.info("Adding number of times the pair was executed together")
        with_times_executed = (
            pair.groupBy("month", "day", "key", "previous_key", "before_previous_key")
            .agg(F.count("previous_key").alias("times"))
            .sort("key", "times")
        )

        with_times_executed.cache()
        with_times_executed.count()

        logging.info("Adding label")

        # add the label
        # divides by the number of executions in the same time period
        dataset = with_times_executed.withColumn('total_day', F.sum('times').over(Window.partitionBy('month', 'day')))
        print('Normalize label on percentage terms')
        dataset = dataset.withColumn("label", (F.col("times") / F.col("total_day")) * F.lit(1000))


        logging.info("TrainingDataset ready, writing it to disk")
        if write_cache:
            self._write_cache(dataset)

        logging.info("Printing a sample of the dataset")
        dataset.show(10)

        return dataset

    @timeit
    def _join_with_previous(self, df):
        """Adds the previou_key as an entry"""
        # build pair dataset with label
        # add literal column
        search_performed_df_tmpcol = df.withColumn("tmp", F.lit("toremove"))
        window = Window.partitionBy("tmp").orderBy("timestamp")

        # add row number to the dataset
        search_performed_df_row_number = search_performed_df_tmpcol.withColumn(
            "row_number", F.row_number().over(window)
        ).sort("timestamp", ascending=False)

        # add previous key to the dataset
        search_performed_df_with_previous = (
            search_performed_df_row_number
            .withColumn(
                "previous_key", F.lag("key", 1, None).over(window)
            )
            .withColumn(
                "before_previous_key", F.lag("key", 2, None).over(window)
            )
            .sort("timestamp", ascending=False)
        )

        return search_performed_df_with_previous

    def _write_cache(self, dataset) -> None:
        print("Writing cache dataset to disk")
        if os.path.exists(TrainingDataset.DATASET_CACHE_FILE):
            import shutil

            shutil.rmtree(TrainingDataset.DATASET_CACHE_FILE)

        dataset.write.parquet(TrainingDataset.DATASET_CACHE_FILE)

    def _read_cache(self) -> Optional[DataFrame]:
        if os.path.exists(TrainingDataset.DATASET_CACHE_FILE):
            print("Reading cache dataset")
            return self._spark.read.parquet(TrainingDataset.DATASET_CACHE_FILE)
        else:
            print("Cache does not exist, creating dataset")


if __name__ == "__main__":
    import fire

    fire.Fire()
