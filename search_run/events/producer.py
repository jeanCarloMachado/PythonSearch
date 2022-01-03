import datetime
import json

from kafka import KafkaProducer

default_port = "9092"
host = f"localhost:{default_port}"


class Producer:
    def __init__(self):
        self.producer = KafkaProducer(bootstrap_servers=host)

    def send(self, topic_name: str, message: dict):
        now = datetime.datetime.now().isoformat()
        message["date_produced"] = now
        self.producer.send(topic_name, json.dumps(message).encode())
