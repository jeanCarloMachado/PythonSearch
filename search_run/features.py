class FeaturesSupport:
    """
    Enables us to have the core behaviour working without the latest in development features.[

    """

    DEFAULT_SUPPORT = {
        "redis": False,
    }

    @staticmethod
    def default():
        return FeaturesSupport(FeaturesSupport.DEFAULT_SUPPORT)

    def __init__(self, config: dict):
        self.supported_config = config

    def is_enabled(self, feature_name) -> bool:
        if feature_name not in self.supported_config:
            raise Exception(f"Feature {feature_name} not configured")

        return self.supported_config[feature_name]
