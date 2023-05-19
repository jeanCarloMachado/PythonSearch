from __future__ import annotations

from python_search.configuration.data_config import DataConfig
from python_search.data_collector import GenericDataCollector


class EntryExecutedDataset:
    """
    Poit of access for the searches performed
    This is the place to keep the source of truth for the schema as well
    """

    columns = ["key", "query_input", "shortcut", "rank_uuid", "timestamp"]
    FILE_NAME = "searches_performed_clean"
    NEW_FILE_NAME = "searches_performed"
    CLEAN_PATH = DataConfig.BASE_DATA_FOLDER + "/" + FILE_NAME
    SCHEMA = None

    def __init__(self, spark=None):
        # For illustrative purposes.
        from pyspark.sql.types import StructType, StructField, StringType, IntegerType
        from pyspark.sql.session import SparkSession

        self.SCHEMA = StructType(
            [
                StructField("key", StringType(), True),
                StructField("query_input", StringType(), True),
                StructField("shortcut", StringType(), True),
                StructField("rank_uuid", StringType(), True),
                StructField("rank_position", IntegerType(), True),
                StructField("timestamp", StringType(), True),
                StructField("earliest_time", StringType(), True),
                StructField("after_execution_time", StringType(), True),
            ]
        )
        self.spark = spark if spark else SparkSession.builder.getOrCreate()

    def load_old(self):
        """
        Load old original events stored via spark-streaming
        """
        data_location = "file://" + DataConfig.OLD_SEARCH_RUNS_PERFORMED_FOLDER
        print("Loading data from: {}".format(data_location))

        return self.spark.read.format("parquet").load_old(data_location)

    def load_clean(self):
        return (
            self.spark.read.format("parquet")
            .schema(EntryExecutedDataset().SCHEMA)
            .load(self.CLEAN_PATH)
        )

    def load_new(self):
        """ "
        Return entries executed data as pyspark
        """
        from pyspark.sql.session import SparkSession

        spark = SparkSession.builder.getOrCreate()
        result_df = spark.read.json(
            self.load_new_path(),
            schema=EntryExecutedDataset().SCHEMA,
        )

        return result_df

    @staticmethod
    def load_new_path():
        return GenericDataCollector().data_location(EntryExecutedDataset.NEW_FILE_NAME)
