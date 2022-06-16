import json
import logging

from kafka import KafkaProducer

from search_run.config import KafkaConfig


class EventProducer:
    """Produce kafka messages"""

    def __init__(self):
        try:
            self.producer = KafkaProducer(bootstrap_servers=KafkaConfig.host)
        except Exception:
            self.producer = None

    def send_object(self, event_object):
        topic_name = type(event_object).__name__
        logging.info(f"Topic: {topic_name}")
        self.send(topic_name, event_object.__dict__)

    def send(self, topic_name: str, message: dict):
        if not self.producer:
            logging.warning("Could not create kakfa producer, not sending messages")
            return

        self.producer.send(topic_name, json.dumps(message).encode())
