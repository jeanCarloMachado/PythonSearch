import json
import logging

from kafka import KafkaProducer

from search_run.config import KafkaConfig


class EventProducer:
    """ Produce kafka messages """

    def __init__(self):
        self.producer = KafkaProducer(bootstrap_servers=KafkaConfig.host)

    def send_object(self, event_object):
        topic_name = type(event_object).__name__
        logging.info(f"Topic: {topic_name}")
        self.send(topic_name, event_object.__dict__)

    def send(self, topic_name: str, message: dict):
        self.producer.send(topic_name, json.dumps(message).encode())
