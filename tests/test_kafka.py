import unittest

from kafka import KafkaConsumer, KafkaProducer

default_port = "9092"
host = f"localhost:{default_port}"


def test_produce():
    producer = KafkaProducer(bootstrap_servers=host)
    producer.send("mytopic", b"messagebytes")


def test_consume():
    """
    Depends that the test above succeeds
    """
    consumer = KafkaConsumer("mytopic", bootstrap_servers=host)
    msg = next(consumer)
    print(msg)
