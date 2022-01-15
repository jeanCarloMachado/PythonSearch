import redis

host = "localhost"
port = 6378
key_name = "test_last_consumed_keys"


def get_redis_client():
    return redis.StrictRedis(host=host, port=port)


def test_write_to_redis():
    redis_client = get_redis_client()
    redis_client.lpush(key_name, "enable_sentry_remote_mode")


def test_read_from_redis():
    redis_client = get_redis_client()
    result = redis_client.lrange(key_name, 0, 10)
    return result


if __name__ == "__main__":
    import fire

    fire.Fire()
