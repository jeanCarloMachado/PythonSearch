import redis

host = "localhost"
port = 6378
key_name = "test_last_consumed_keys"


def get_redis_client():
    return redis.StrictRedis(host=host, port=port)


class LatestUsed:
    """ Contains the logic to read and write the  latest used keys from redis """

    def __init__(self, key_name="latest_consumed_key"):
        self.redis_key_name = key_name
        self.redis_client = get_redis_client()

    def write_last_used_key(self, value: str):
        self.redis_client.lpush(self.redis_key_name, value)


def test_write_to_redis():
    LatestUsed(key_name=key_name).write_last_used_key("enable_sentry_remote_mode")


def test_read_from_redis():
    redis_client = get_redis_client()
    result = redis_client.lrange(key_name, 0, 10)
    return result


if __name__ == "__main__":
    import fire

    fire.Fire()
