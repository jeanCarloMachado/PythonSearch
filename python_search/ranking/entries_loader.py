from typing import List


class EntriesLoader:
    """Class to access the current existing key"""

    @staticmethod
    def load_all_keys() -> List[str]:
        from entries_main import config

        return list(config.commands.keys())
