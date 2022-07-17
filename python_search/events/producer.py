import json
import logging

from kafka import KafkaProducer

from python_search.config import KafkaConfig


class EventProducer:
    """Produce kafka messages"""

    def __init__(self):

        try:
            self.producer = KafkaProducer(
                bootstrap_servers=KafkaConfig.host,
                acks=0,
                max_block_ms=1000,
                request_timeout_ms=500,
            )
        except Exception as e:
            logging.info("Could not create kafka producer, not sending messages")
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
        self.producer.flush()
