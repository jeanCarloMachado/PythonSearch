from typing import List


class EntriesLoader:
    """Class to acccess the current existing key"""

    @staticmethod
    def load_all_keys() -> List[str]:
        from entries.main import config

        return list(config.commands.keys())