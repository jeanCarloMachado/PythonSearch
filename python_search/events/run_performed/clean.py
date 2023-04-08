import pyspark.sql.functions as F
import os


class RunPerformedCleaning:
    def clean(self):
        print("Performing the cleaning of the new events")
        from python_search.events.run_performed.dataset import EntryExecutedDataset

        max_timestamp = None

        if os.path.exists(EntryExecutedDataset().CLEAN_PATH):
            # load baseline clean
            df_clean = EntryExecutedDataset().load_clean()
            print("Clean schema")
            df_clean.printSchema()
            print(f"Number of pre-existing clean events: {df_clean.count()}")

            # get latest timestamp imported
            max_timestamp = df_clean.agg({"timestamp": "max"}).collect()[0][0]

        df_new = EntryExecutedDataset().load_new().sort("timestamp", ascending=False)
        df_new = df_new.withColumn(
            "timestamp_real", F.from_unixtime(F.col("timestamp"))
        )

        if max_timestamp:
            df_new = df_new.filter("timestamp IS NOT NULL").filter(
                f"timestamp_real > '{max_timestamp}'"
            )
        df_new = df_new.drop("timestamp")
        df_new = df_new.withColumnRenamed("timestamp_real", "timestamp")
        df_new = df_new.withColumn("date", F.to_date("timestamp"))

        print(f"Number of new events: {df_new.count()}")

        print("New schema")
        df_new.printSchema()

        if os.path.exists(EntryExecutedDataset().CLEAN_PATH):
            joined = df_clean.union(df_new)
            joined.write.option("partitionOverwriteMode", "dynamic").partitionBy(
                "date"
            ).mode("overwrite").parquet(EntryExecutedDataset.CLEAN_PATH)
        else:
            df_new.write.option("partitionOverwriteMode", "dynamic").partitionBy(
                "date"
            ).mode("overwrite").parquet(EntryExecutedDataset.CLEAN_PATH)

        df_clean = EntryExecutedDataset().load_clean()
        print("Number of clean events", df_clean.count())


if __name__ == "__main__":
    RunPerformedCleaning().clean()
