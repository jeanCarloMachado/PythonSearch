import datetime

import pyspark.sql.functions as F
from kafka import KafkaConsumer, KafkaProducer

default_port = "9092"
host = f"localhost:{default_port}"
topic_name = "mytopic"


def test_produce():
    now = datetime.datetime.now().isoformat()
    producer = KafkaProducer(bootstrap_servers=host)
    producer.send(
        topic_name, f'{{"message": "another message", "my_date": "{now}"}}'.encode()
    )


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

    To trigger run the following:
    spark-submit --packages org.apache.spark:spark-sql-kafka-0-10_2.12:3.0.1 tests/test_kafka.py test_consume_spark
    """
    import findspark

    findspark.init()
    from pyspark.sql.session import SparkSession

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
        "value_as_json", F.from_json("value_decoded", "message String, query string")
    )
    df = df.select("value_as_json.*", "timestamp")

    streamingQuery = (
        df.writeStream.format("parquet")
        .outputMode("append")
        .option("path", f"/data/python_search/data_warehouse/dataframes/{topic_name}")
        .option(
            "checkpointLocation",
            f"/data/python_search/data_warehouse/checkpoints/{topic_name}",
        )  # write-ahead logs for
        .trigger(processingTime="1 second")
        .start()
    )

    streamingQuery.awaitTermination()


if __name__ == "__main__":
    import fire

    fire.Fire()
