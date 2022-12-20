import json
import os

from python_search.logger import setup_data_writter_logger


class GenericDataCollector:
    """
    A generic data writer component that works tightly integrated with spark
    """

    BASE_DATA_DESTINATION_DIR = os.environ["HOME"] + "/.data/data_collection"

    @staticmethod
    def initialize():
        import fire

        return fire.Fire(GenericDataCollector())

    def write(self, *, data: dict, table_name: str, date=None):
        self.logger = setup_data_writter_logger(table_name)
        from datetime import datetime

        datetime.now().timestamp()

        import os

        os.system(
            f"mkdir -p {GenericDataCollector.BASE_DATA_DESTINATION_DIR}/{table_name}"
        )
        import datetime

        file_name = f"{self.data_location(table_name)}/{datetime.datetime.now(datetime.timezone.utc).timestamp()}.json"

        with open(file_name, "w") as f:
            f.write(json.dumps(data))

        self.logger.info(f"File {file_name} written successfully with data {data}")

    def data_location(self, table_name) -> str:
        return f"{GenericDataCollector.BASE_DATA_DESTINATION_DIR}/{table_name}"

    def dataframe(self, table_name):
        from pyspark.sql import DataFrame
        from pyspark.sql.session import SparkSession

        spark = SparkSession.builder.getOrCreate()
        result: DataFrame = spark.read.json(GenericDataCollector().data_location(table_name))
        return result

    def show_data(self, table_name):
        return self.dataframe(table_name).show()


if __name__ == "__main__":
    GenericDataCollector.initialize()
