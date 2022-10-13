from __future__ import annotations

from typing import Optional

from pydantic import BaseModel
from pyspark.sql.types import (StringType, StructField, StructType,
                               TimestampType)

from python_search.config import DataConfig
from python_search.data_collector import GenericDataCollector


class RunPerformedDataset:
    """
    Poit of acess for the searches performed
    This is the place to keep the source of truth for the schema as well
    """

    columns = ["key", "query_input", "shortcut", "timestamp"]

    def __init__(self, spark=None):
        from pyspark.sql.session import SparkSession

        self.spark = spark if spark else SparkSession.builder.getOrCreate()

    def load(self):
        data_location = "file://" + DataConfig.SEARCH_RUNS_PERFORMED_FOLDER
        print("Loading data from: {}".format(data_location))
        return self.spark.read.format("parquet").load(data_location)

    def load_new(self):
        return GenericDataCollector().dataframe("searches_performed")


class RunPerformedWriter:
    def write(self, event: RunPerformed):
        import datetime;
        event.timestamp  = str(datetime.datetime.now(datetime.timezone.utc).timestamp())

        return GenericDataCollector().write(
            data=event.__dict__, table_name="searches_performed"
        )


class RunPerformed(BaseModel):
    """
    Main event of the application.
    Identifies a search being executed
    """

    # name of the entry matched
    key: str
    # for when a query was typed by the user
    # @todo rename to something more meaningful
    query_input: str
    # for when it is started from a shortcut
    shortcut: str
    # unix timestamp
    timestamp: Optional[str] = None

    @staticmethod
    def get_schema():
        return "key string, query_input string, shortcut string"


class LogSearchRunPerformedClient:
    def send(self, data: RunPerformed):
        import requests

        try:
            return requests.post(
                url="http://localhost:8000/log_run", json=data.__dict__
            )
        except BaseException as e:
            print(f"Logging results failed, reason: {e}")
