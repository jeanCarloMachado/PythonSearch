#!/usr/bin/env python3

from typing import List

class LatestUsedEntries:
    """
    Contains the latest used keys and the API to add new ones.
    """

    _used_keys = []

    def get_latest_used_keys(self) -> List[str]:
        """
        return a list of unike used keys ordered by the last time they were used
        the most recent in the top.
        """
        return LatestUsedEntries._used_keys

    @staticmethod
    def add_latest_used(key):
        """adds to the list"""
        LatestUsedEntries._used_keys = [key] + LatestUsedEntries._used_keys


if __name__ == "__main__":
    import fire

    fire.Fire(LatestUsedEntries)
