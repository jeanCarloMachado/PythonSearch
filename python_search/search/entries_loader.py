from typing import List

from python_search.configuration.loader import ConfigurationLoader
from python_search.core_entities.core_entities import Entry


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

    def load_entries(self) -> dict:
        return EntriesLoader.load_all_entries()

    def load_entries_as_json(self):
        import json

        result = {}
        for entry in EntriesLoader.load_all_entries():
            result[entry.key] = entry.get_serialized_value()

        return json.dumps(result)

    @staticmethod
    def load_privacy_neutral_only() -> List[Entry]:
        from python_search.privacy.privacy_detector import PrivacyDetector

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
        return EntriesLoader.convert_to_list_of_entries(entries)

    @staticmethod
    def convert_to_list_of_entries(entries: dict) -> List[Entry]:
        for key, value in entries.items():
            yield Entry(key, value)


if __name__ == "__main__":
    import fire

    fire.Fire(EntriesLoader)
