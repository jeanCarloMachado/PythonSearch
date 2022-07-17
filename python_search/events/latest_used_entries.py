#!/usr/bin/env python3

import json
import logging
import sys

from kafka import KafkaConsumer

from python_search.config import KafkaConfig
from python_search.infrastructure.redis import PythonSearchRedis


class LatestUsedEntries:
    """
    Contains the logic to read and write the  latest used keys from redis
    These entries are then applied to the ranking.
    """

    MAX_PERSISTED_ITEMS = 1000
    NUMBER_OF_KEYS_TO_RETRIEVE = 100

    def __init__(self, key_name="latest_consumed_key"):
        logging.basicConfig(
            level=logging.INFO, handlers=[logging.StreamHandler(sys.stdout)]
        )

        self.redis_key_name = key_name
        self.redis_client = LatestUsedEntries.get_redis_client()

    @staticmethod
    def get_redis_client():
        return PythonSearchRedis.get_client()

    def get_latest_used_keys(self):
        """
        return a list of unike used keys ordered by the last time they were used
        the most recent in the top.
        """
        result = self.redis_client.lrange(
            LatestUsedEntries().redis_key_name,
            0,
            LatestUsedEntries.NUMBER_OF_KEYS_TO_RETRIEVE,
        )

        result = [x.decode() for x in result]
        result = list(dict.fromkeys(result))
        return result

    def write_last_used_key(self, value: str):
        self.redis_client.lpush(self.redis_key_name, value)
        self.redis_client.ltrim(self.redis_key_name, 0, self.MAX_PERSISTED_ITEMS)

    def consume(self):
        print("Starting kafka cosumer")
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
            if not message.value["shortcut"]:
                logging.info(f"THE key: {key_executed} will be persisted in redis")
                self.write_last_used_key(key_executed)
            else:
                logging.info(
                    f"THE key: {key_executed} will be skipped as it is a shortcut"
                )


if __name__ == "__main__":
    import fire

    fire.Fire(LatestUsedEntries)
