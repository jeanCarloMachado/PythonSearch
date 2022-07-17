from python_search.events.consumer import SparkEventConsumer
from python_search.events.latest_used_entries import LatestUsedEntries
from python_search.events.producer import EventProducer

topic_name = "mytopic"


def test_produce():
    EventProducer().send(topic_name, {"message": "another message"})


def test_consume_spark():
    """
    Just tests if the class is callable as it depends of spark-submit to actually run
    """
    assert callable(SparkEventConsumer().consume)


def test_consume_kafka():
    assert callable(LatestUsedEntries().consume)


if __name__ == "__main__":
    import fire

    fire.Fire()
