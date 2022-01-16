import json

import redis
from kafka import KafkaConsumer

from search_run.config import KafkaConfig, RedisConfig


class LatestUsedEntries:
    """ Contains the logic to read and write the  latest used keys from redis """

    MAX_PERSISTED_ITEMS = 1000

    def __init__(self, key_name="latest_consumed_key"):
        self.redis_key_name = key_name
        self.redis_client = LatestUsedEntries.get_redis_client()

    @staticmethod
    def get_redis_client():
        return redis.StrictRedis(host=RedisConfig.host, port=RedisConfig.port)

    def get_latest_used_keys(self):
        result = self.redis_client.lrange(LatestUsedEntries().redis_key_name, 0, 50)
        result = [x.decode() for x in result]
        # result = list(dict.fromkeys(result))
        return result

    def write_last_used_key(self, value: str):
        self.redis_client.lpush(self.redis_key_name, value)
        self.redis_client.ltrim(self.redis_key_name, 0, self.MAX_PERSISTED_ITEMS)

    def consume(self):
        consumer = KafkaConsumer(
            "SearchRunPerformed",
            bootstrap_servers=KafkaConfig.host,
            auto_offset_reset="earliest",
            enable_auto_commit=True,
            group_id="to_redis",
            value_deserializer=lambda x: json.loads(x.decode("utf-8")),
        )

        for message in consumer:
            key_executed = message.value["key"]
            print(f"THE key: {key_executed} ")
            self.write_last_used_key(key_executed)
