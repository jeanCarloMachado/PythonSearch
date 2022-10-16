from __future__ import annotations

from python_search.config import DataConfig
from python_search.data_collector import GenericDataCollector


class RunPerformedDataset:
    """
    Poit of acess for the searches performed
    This is the place to keep the source of truth for the schema as well
    """

    columns = ["key", "query_input", "shortcut", "timestamp"]
    CLEAN_PATH = DataConfig.CLEAN_EVENTS_FOLDER + "/run_performed"

    def __init__(self, spark=None):
        from pyspark.sql.session import SparkSession

        self.spark = spark if spark else SparkSession.builder.getOrCreate()

    def load_old(self):
        """
        Load old original events stored via spark-streammnig
        """
        data_location = "file://" + DataConfig.SEARCH_RUNS_PERFORMED_FOLDER
        print("Loading data from: {}".format(data_location))
        return self.spark.read.format("parquet").load_old(data_location)

    def load_clean(self):
        return self.spark.read.parquet(self.CLEAN_PATH)

    def load_new(self):
        return GenericDataCollector().dataframe("searches_performed")
