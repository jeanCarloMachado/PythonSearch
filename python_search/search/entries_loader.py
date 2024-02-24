from typing import List

from python_search.configuration.loader import ConfigurationLoader
from python_search.core_entities.core_entities import Entry
from python_search.privacy.privacy_detector import PrivacyDetector


class EntriesLoader:
    """Class to access the current existing key"""

    @staticmethod
    def load_only_keys() -> List[str]:
        """
        Return just the key names strings
        """
        keys = list(ConfigurationLoader().load_entries().keys())

        print("Loaded in total " + str(len(keys)) + " keys")

        return keys

    @staticmethod
    def load_privacy_neutral_only() -> List[Entry]:
        detector = PrivacyDetector()

        for i in EntriesLoader.load_all_entries():
            if not detector.has_sentitive_content(
                i.get_content_str()
            ) and not detector.has_sentitive_content(i.key):
                yield i

    @staticmethod
    def load_all_entries() -> List[Entry]:
        """
        Return just the key names strings
        """

        entries = ConfigurationLoader().load_entries()

        for key, value in entries.items():
            yield Entry(key, value)
