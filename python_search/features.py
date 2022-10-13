class PythonSearchFeaturesSupport:
    """
    Enables us to have the core behaviour working without the latest in development features.

    """

    DYNAMIC_RANKING = "dynamic_ranking"

    DEFAULT_SUPPORT = {
        # if user history or is supported
        DYNAMIC_RANKING: False,
    }

    @staticmethod
    def default():
        return PythonSearchFeaturesSupport(PythonSearchFeaturesSupport.DEFAULT_SUPPORT)

    def __init__(self, config: dict):
        self.supported_config = {
            **PythonSearchFeaturesSupport.DEFAULT_SUPPORT,
            **config,
        }

    def is_enabled(self, feature_name) -> bool:
        if feature_name not in self.supported_config:
            raise Exception(f"Feature {feature_name} not configured")

        return self.supported_config[feature_name]

    def is_dynamic_ranking_supported(self):
        return self.is_enabled("dynamic_ranking")

    def is_redis_supported(self):
        return self.is_enabled("redis")
