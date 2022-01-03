#!/usr/bin/env python
from pyspark.sql import SparkSession
from pyspark.sql import functions as F

default_port = "9092"
host = f"localhost:{default_port}"


class EventConsumer:
    """ Listen to kafka events and store then in the data-wharehouse """

    def __init__(self, disable_await_termination=False):
        # by defualt awaits termination
        self.await_termination = not disable_await_termination

    def consume(self, topic_name):
        """
        To trigger run the followingxjujjj:
        spark-submit --packages org.apache.spark:spark-sql-kafka-0-10_2.12:3.0.1 /home/jean/projects/PythonSearch/search_run/events/consumer.py consume mytopic
        """

        spark = SparkSession.builder.getOrCreate()
        df = (
            spark.readStream.format("kafka")
            .option("kafka.bootstrap.servers", host)
            .option("subscribe", topic_name)
            .load()
        )
        df.printSchema()
        # process the data here
        df = df.selectExpr("CAST(value as STRING) as value_decoded", "timestamp")
        df = df.withColumn(
            "value_as_json",
            F.from_json("value_decoded", "message String, query string"),
        )
        df = df.select("value_as_json.*", "timestamp")

        streamingQuery = (
            df.writeStream.format("parquet")
            .outputMode("append")
            .option(
                "path", f"/data/python_search/data_warehouse/dataframes/{topic_name}"
            )
            .option(
                "checkpointLocation",
                f"/data/python_search/data_warehouse/checkpoints/{topic_name}",
            )  # write-ahead logs for
            .trigger(processingTime="1 second")
            .start()
        )

        if self.await_termination:
            streamingQuery.awaitTermination()


if __name__ == "__main__":
    import fire

    fire.Fire(EventConsumer)
