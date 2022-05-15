class SearchesPerformed:
    """
    Poit of acess for the searches performed
    This is the place to keep the source of truth for the schema as well
    """

    def __init__(self, spark=None):
        from pyspark.sql.session import SparkSession

        self.spark = spark if spark else SparkSession.builder.getOrCreate()

    def load(self):
        return self.spark.read.format("parquet").load(
            f"/data/python_search/data_warehouse/dataframes/SearchRunPerformed"
        )
