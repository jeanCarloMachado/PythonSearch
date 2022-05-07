class PythonSearchRedis:
    @staticmethod
    def get_client():
        import redis

        from search_run.config import RedisConfig

        return redis.StrictRedis(host=RedisConfig.host, port=RedisConfig.port)
