import datetime

from kafka import KafkaConsumer, KafkaProducer

from search_run.events.consumer import EventConsumer

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
    """
    EventConsumer().consume(topic_name)


if __name__ == "__main__":
    import fire

    fire.Fire()
