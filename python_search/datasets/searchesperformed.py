from python_search.config import DataConfig

from pyspark.sql.types import *

class SearchesPerformed:
    """
    Poit of acess for the searches performed
    This is the place to keep the source of truth for the schema as well
    """

    columns = ["key", "query_input", "shortcut", "timestamp"]

    def __init__(self, spark=None):
        from pyspark.sql.session import SparkSession

        self.spark = spark if spark else SparkSession.builder.getOrCreate()

    def load(self):

        my_schema = StructType(
            [StructField('key', StringType(), True),
             StructField('query_input', StringType(), True),
             StructField('shortcut', StringType(), True),
             StructField('timestamp', TimestampType(), True),
             ])


        data_location = "file://" + DataConfig.SEARCH_RUNS_PERFORMED_FOLDER
        print("Loading data from: {}".format(data_location))
        return self.spark.read.format("parquet").load(
            data_location

        )
