import json
import os

from python_search.logger import setup_data_writter_logger


class GenericDataCollector:
    """
    A generic data writer component that works tightly integrated with spark
    """

    BASE_DATA_DESTINATION_DIR = os.environ["HOME"] + "/.python_search/data/"

    def __init__(self, *, base_location=None):
        self.base_location = (
            base_location
            if base_location
            else GenericDataCollector.BASE_DATA_DESTINATION_DIR
        )

    @staticmethod
    def initialize():
        import fire

        return fire.Fire(GenericDataCollector())

    def write(self, *, data: dict, table_name: str, date=None):
        self.logger = setup_data_writter_logger(table_name)
        from datetime import datetime

        datetime.now().timestamp()

        os.system(f"mkdir -p {self.base_location}/{table_name}")
        import datetime

        file_name = f"{self.data_location(table_name)}/{datetime.datetime.now(datetime.timezone.utc).timestamp()}.json"

        with open(file_name, "w") as f:
            f.write(json.dumps(data))

        self.logger.info(f"File {file_name} written successfully with data {data}")

    def data_location(self, table_name) -> str:
        return f"{self.base_location}/{table_name}"

    def dataframe(self, table_name):
        from pyspark.sql import DataFrame
        from pyspark.sql.session import SparkSession

        spark = SparkSession.builder.getOrCreate()
        result: DataFrame = spark.read.json(self.data_location(table_name))
        return result

    def show_data(self, table_name):
        return self.dataframe(table_name).show()


if __name__ == "__main__":
    GenericDataCollector.initialize()
