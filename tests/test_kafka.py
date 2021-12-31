import os
import unittest

from kafka import KafkaConsumer, KafkaProducer
from pyspark.sql.session import SparkSession

default_port = "9092"
host = f"localhost:{default_port}"
topic_name = "mytopic"


def test_produce():
    print("test")
    producer = KafkaProducer(bootstrap_servers=host)
    producer.send(topic_name, b"messagebytes")


def test_consume_kafka():
    """
    Depends that the test above succeeds
    """
    consumer = KafkaConsumer(topic_name, bootstrap_servers=host)
    msg = next(consumer)
    print(msg)


def test_consume_spark():
    """
    Depends that the test above succeeds
    """

    # spark_version = '3.2.0'
    # os.environ['PYSPARK_SUBMIT_ARGS'] = '--packages org.apache.spark:spark-sql-kafka-0-10_2.12:{}'.format(
    # spark_version)
    spark = SparkSession.builder.getOrCreate()
    df = (
        spark.readStream.format("kafka")
        .option("kafka.bootstrap.servers", host)
        .option("subscribe", topic_name)
        .load()
    )
    # process the data here
    counts = df.count()

    checkpointDir = "/tmp/kafka"
    streamingQuery = (
        counts.writeStrem.format("console")
        .outputMode("complete")
        .trigger(processingTime="1 second")
        .option("checkpointLocation", checkpointDir)
        .start()
    )

    streamingQuery.awaitTermination()


if __name__ == "__main__":
    import fire

    fire.Fire()
