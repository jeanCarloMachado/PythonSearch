from __future__ import annotations

from pyspark.sql.types import StructType, StructField, StringType, IntegerType

from python_search.config import DataConfig
from python_search.data_collector import GenericDataCollector


class EntryExecutedDataset:
    """
    Poit of access for the searches performed
    This is the place to keep the source of truth for the schema as well
    """

    columns = ["key", "query_input", "shortcut", "rank_uuid", "timestamp"]
    TABLE_NAME = "run_performed"
    NEW_TABLE_NAME = "searches_performed"
    CLEAN_PATH = DataConfig.CLEAN_EVENTS_FOLDER + "/" + TABLE_NAME

    def __init__(self, spark=None):
        from pyspark.sql.session import SparkSession

        self.spark = spark if spark else SparkSession.builder.getOrCreate()

    def load_old(self):
        """
        Load old original events stored via spark-streaming
        """
        data_location = "file://" + DataConfig.SEARCH_RUNS_PERFORMED_FOLDER
        print("Loading data from: {}".format(data_location))
        return self.spark.read.format("parquet").load_old(data_location)

    def load_clean(self):
        return self.spark.read.parquet(self.CLEAN_PATH)

    def load_new(self):
        from pyspark.sql.session import SparkSession

        schema = StructType(
            [
                StructField("key", StringType(), True),
                StructField("query_input", StringType(), True),
                StructField("shortcut", StringType(), True),
                StructField("rank_uuid", StringType(), True),
                StructField("rank_position", IntegerType(), True),
                StructField("timestamp", StringType(), True),
            ]
        )

        spark = SparkSession.builder.getOrCreate()
        result_df = spark.read.json(
            GenericDataCollector().data_location(EntryExecutedDataset.NEW_TABLE_NAME),
            schema=schema,
        )

        return result_df
