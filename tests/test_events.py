from search_run.events.consumer import EventConsumer
from search_run.events.producer import EventProducer

topic_name = "mytopic"


def test_produce():
    EventProducer().send(topic_name, {"message": "another message"})


def test_consume_spark():
    """
    Just tests if the class is callable as it depends of spark-submit to actually run
    """
    assert callable(EventConsumer().consume)


if __name__ == "__main__":
    import fire

    fire.Fire()
