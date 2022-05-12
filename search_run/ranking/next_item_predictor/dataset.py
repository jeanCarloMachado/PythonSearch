import logging
import os.path
import sys

import pyspark.sql.functions as F
from pyspark.sql import SparkSession
from pyspark.sql.window import Window

from search_run.datasets.searchesperformed import SearchesPerformed


class Dataset:
    """
    Builds the dataset ready for training
    """

    def __init__(self):
        self._spark = SparkSession.builder.getOrCreate()

    def build(self, use_cache=False):
        """When cache is enabled, writes a parquet in a temporay file"""
        if use_cache:
            if os.path.exists("/tmp/dataset"):
                print("Reading cache dataset")
                return self._spark.read.parquet("/tmp/dataset")
            else:
                print("Cache does not exist, creating dataset")

        logging.basicConfig(
            level=logging.INFO, handlers=[logging.StreamHandler(sys.stdout)]
        ),

        df = SearchesPerformed(self._spark).load()
        logging.info("Loading searches performed")
        df.sort("timestamp", ascending=False).show()

        # build pair dataset with label
        # add literal column
        df = df.withColumn("tmp", F.lit("toremove"))
        window = Window.partitionBy("tmp").orderBy("timestamp")

        # add row number to the dataset
        df = df.withColumn("row_number", F.row_number().over(window)).sort(
            "timestamp", ascending=False
        )

        # add previous key to teh dataset
        df = df.withColumn("previous_key", F.lag("key", 1, None).over(window)).sort(
            "timestamp", ascending=False
        )
        logging.info("Columns added")
        # filter only necessary columns
        pair = df.select("key", "previous_key", "timestamp")

        logging.info("Adding number of times the pair was executed together")
        grouped = (
            pair.groupBy("key", "previous_key")
            .agg(F.count("previous_key").alias("times"))
            .sort("key", "times")
        )

        grouped.cache()
        grouped.count()

        logging.info("Adding label")
        # add the label
        dataset = grouped.withColumn(
            "label", F.col("times") / F.sum("times").over(Window.partitionBy("key"))
        ).orderBy("key")
        dataset = dataset.select("key", "previous_key", "label")
        dataset = dataset.filter("LENGTH(key) > 1")

        logging.info("Dataset ready, writing it to disk")
        if use_cache:
            print("Writing cache dataset to disk")
            if os.path.exists("/tmp/dataset"):
                os.remove("/tmp/dataset")
            dataset.write.parquet("/tmp/dataset")

        return dataset


if __name__ == "__main__":
    import fire

    fire.Fire()
