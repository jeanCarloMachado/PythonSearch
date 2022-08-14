import logging
import os


class FeaturesSupport:
    """
    Enables us to have the core behaviour working without the latest in development features.[

    """

    DYNAMIC_RANKING = "dynamic_ranking"

    DEFAULT_SUPPORT = {
        # if the ml ranking should be used or not
        # if user history or is supported
        DYNAMIC_RANKING: False,
        # turn on if you have a redis instance to improve the ranking
        "redis": False,
        # turn to true if you want data to be collected
        "event_tracking": False,
    }

    @staticmethod
    def default():
        return FeaturesSupport(FeaturesSupport.DEFAULT_SUPPORT)

    def __init__(self, config: dict):
        self.supported_config = {**FeaturesSupport.DEFAULT_SUPPORT, **config}

    def is_enabled(self, feature_name) -> bool:
        if feature_name not in self.supported_config:
            raise Exception(f"Feature {feature_name} not configured")

        return self.supported_config[feature_name]

    def is_dynamic_ranking_supported(self):
        return self.is_enabled("dynamic_ranking")

    def is_redis_supported(self):
        return self.is_enabled("redis")


class FeatureToggle:
    """
    A simple feature toggle abstraction that allows one to turn on/off features for their environment without touching code.
    """

    def __init__(self):
        self.BASE_PATH = f"{os.getenv('HOME')}/.PythonSearch/features"

    def enable(self, feature_name: str):
        os.system(f"touch {self.BASE_PATH}/{feature_name}")

    def disable(self, feature_name: str):
        os.system(f"rm {self.BASE_PATH}/{feature_name}")

    def is_enabled(self, feature_name: str) -> bool:
        result = 0 == os.system(f" test -f {self.BASE_PATH}/{feature_name}")

        if result:
            logging.debug(f"Feature toggle {feature_name} is enabled")
        else:
            logging.debug(f"Feature toggle {feature_name} is disabled")

        return result
