#!/usr/bin/env python
from python_search.config import RedisConfig


class PythonSearchRedis:
    @staticmethod
    def get_client():
        import redis

        return redis.StrictRedis(host=RedisConfig.host, port=RedisConfig.port)


class RedisCli:
    def cli(self):
        import os

        os.system(f"redis-cli -h {RedisConfig.host} -p {RedisConfig.port}")


if __name__ == "__main__":
    import fire

    fire.Fire(RedisCli)
