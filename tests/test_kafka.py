import os

from kafka import KafkaConsumer, KafkaProducer

default_port = "9092"
host = f"localhost:{default_port}"
topic_name = "mytopic"


def test_produce():
    print("test")
    producer = KafkaProducer(bootstrap_servers=host)
    producer.send(topic_name, b"the message in bytes")


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

    spark_version = "3.0.1"
    os.environ[
        "PYSPARK_SUBMIT_ARGS"
    ] = f"--packages org.apache.spark:spark-sql-kafka-0-10_2.12:{spark_version}"
    spark = SparkSession.builder.getOrCreate()
    df = (
        spark.readStream.format("kafka")
        .option("kafka.bootstrap.servers", host)
        .option("subscribe", topic_name)
        .load()
    )
    # process the data here
    df = df.selectExpr("CAST(value as STRING)")

    streamingQuery = (
        df.writeStream.format("console")
        .outputMode("append")
        .trigger(processingTime="1 second")
        .start()
    )

    streamingQuery.awaitTermination()


if __name__ == "__main__":
    import fire

    fire.Fire()
