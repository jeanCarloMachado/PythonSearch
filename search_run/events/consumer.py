#!/usr/bin/env python
from pyspark.sql import SparkSession
from pyspark.sql import functions as F

from search_run.events.events import SearchRunPerformed

default_port = "9092"
host = f"localhost:{default_port}"


def consume_search_run_performed():
    EventConsumer().from_class(SearchRunPerformed)


class EventConsumer:
    """ Listen to kafka events and store then in the data-wharehouse """

    def __init__(self, disable_await_termination=False):
        # by defalt awaits termination
        self.await_termination = not disable_await_termination

    def from_class(self, class_reference):
        topic_name = class_reference.__name__
        self.consume(topic_name, class_reference.get_schema())

    def consume(self, topic_name, schema):
        """
        To trigger run the following:

        spark-submit \
        --packages org.apache.spark:spark-sql-kafka-0-10_2.12:3.0.1 \
        /home/jean/projects/PythonSearch/search_run/events/consumer.py consume mytopic
        """

        spark = SparkSession.builder.getOrCreate()
        df = (
            spark.readStream.format("kafka")
            .option("kafka.bootstrap.servers", host)
            .option("subscribe", topic_name)
            .load()
        )
        # process the data here
        df = df.selectExpr("CAST(value as STRING) as value_decoded", "timestamp")
        df = df.withColumn(
            "value_as_json",
            F.from_json("value_decoded", schema),
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

    fire.Fire()
