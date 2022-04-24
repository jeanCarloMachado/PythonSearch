class SearchesPerformed:
    def __init__(self, spark):
        self.spark = spark

    def load(self):
        return self.spark.read.format("parquet").load(
            f"/data/python_search/data_warehouse/dataframes/SearchRunPerformed"
        )
