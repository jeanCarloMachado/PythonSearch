from typing import List

from python_search.configuration.loader import ConfigurationLoader
from python_search.core_entities.core_entities import Entry


class EntriesLoader:
    """Class to access the current existing key"""

    @staticmethod
    def load_all_keys() -> List[str]:
        """
        Return just the key names strings
        """
        keys = list(ConfigurationLoader().load_entries().keys())

        print("Loaded in total " + str(len(keys)) + " keys")

        return keys

    @staticmethod
    def load_key_values_str():
        """
        Return just the key names strings
        """

        entries = ConfigurationLoader().load_entries()

        keys = []
        values = []
        for key, value in entries.items():
            entry = Entry(key, value)
            value_str = entry.get_only_content(return_str=True)

            if not key or not value_str:
                continue

            keys.append(key)
            values.append(value_str)

        return keys, values
