import logging
import os


class FeatureToggle:
    """
    A simple feature toggle abstraction that allows one to turn on/off features for their environment without touching code.
    """

    @staticmethod
    def main():
        import fire

        fire.Fire(FeatureToggle)

    def __init__(self):
        self.BASE_PATH = f"{os.getenv('HOME')}/.PythonSearch/features"

        if not os.path.exists(self.BASE_PATH):
            os.system(f"mkdir -p '{self.BASE_PATH}'")

    def enable(self, feature_name: str):
        os.system(f"touch {self.BASE_PATH}/{feature_name}")

    def disable(self, feature_name: str):
        os.system(f"rm {self.BASE_PATH}/{feature_name}")

    def toggle(self, feature_name):
        is_enabled = self.is_enabled(feature_name)
        print(f"feature: {feature_name} is enabled={is_enabled}, inverting it")

        if is_enabled:
            self.disable(feature_name)
        else:
            self.enable(feature_name)

    def is_enabled(self, feature_name: str) -> bool:
        result = 0 == os.system(f" test -f {self.BASE_PATH}/{feature_name}")

        if result:
            logging.debug(f"Feature toggle {feature_name} is enabled")
        else:
            logging.debug(f"Feature toggle {feature_name} is disabled")

        return result
