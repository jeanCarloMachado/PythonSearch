"""
Clients should depend on a configuration instance (config) rather than in the class,
the class should only be used for type annotation.
This way we can have multiple configs depending of the environment.
"""

from python_search.environment import is_mac


class MLFlowConfig:
    port = 5002


class KafkaConfig:
    default_port: str = "9092"
    host: str = f"127.0.0.1:{default_port}"


class RedisConfig:
    host = "127.0.0.1" if is_mac() else "host.docker.internal"
    port = 6379
