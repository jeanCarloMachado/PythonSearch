from typing import List

from python_search.config import ConfigurationLoader


class EntriesLoader:
    """Class to access the current existing key"""

    @staticmethod
    def load_all_keys() -> List[str]:
        keys = list(ConfigurationLoader().load_entries().keys())

        print("Loaded in total " + str(len(keys)) + " keys")

        return keys
