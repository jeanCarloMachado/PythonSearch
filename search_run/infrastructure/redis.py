

def get_redis_client():
    from search_run.config import RedisConfig
    import redis
    return redis.StrictRedis(host=RedisConfig.host, port=RedisConfig.port)