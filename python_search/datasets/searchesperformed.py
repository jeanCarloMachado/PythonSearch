from python_search.config import DataConfig


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
        return self.spark.read.format("parquet").load(
            DataConfig.SEARCH_RUNS_PERFORMED_FOLDER
        )
