from pyspark.sql import functions as F
from pyspark.sql import Window

from python_search.events.run_performed.dataset import EntryExecutedDataset


class PreviousKey:
    def get_previous_n(self, n=1):
        df = EntryExecutedDataset().load_clean()
        df = df.select("key", "timestamp", "rank_uuid")
        df_result = df.withColumn("tmp", F.lit("toremove"))
        window = Window.partitionBy("tmp").orderBy("timestamp")

        for i in range(1, n + 1):
            df_result = df_result.withColumn(
                f"previous_{i}_key", F.lag("key", i, None).over(window)
            ).withColumn(
                f"previous_{i}_timestamp", F.lag("timestamp", i, None).over(window)
            )

        df_result = df_result.filter("rank_uuid is not null")
        df_result = df_result.withColumnRenamed("rank_uuid", "uuid")
        df_result = df_result.sort("timestamp", ascending=False)
        df_result = df_result.drop("tmp")
        return df_result
