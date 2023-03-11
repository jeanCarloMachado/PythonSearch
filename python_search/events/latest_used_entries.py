#!/usr/bin/env python3
import json
import os
from typing import List

from python_search.events.run_performed.dataset import EntryExecutedDataset


class RecentKeys:
    """
    Contains the latest used keys and the API to add new ones.
    """

    _blacklisted_items = ["python search main entry"]
    _used_keys = []

    def get_latest_used_keys(self) -> List[str]:
        """
        return a list of unike used keys ordered by the last time they were used
        the most recent in the top.
        """

        ds = EntryExecutedDataset
        path = ds.load_new_path()

        import glob
        list_of_files = sorted(filter(os.path.isfile,
                                      glob.glob(path + '/*')))

        result = []

        HISTORY_SIZE = 30
        list_of_files = list_of_files[-HISTORY_SIZE:]
        list_of_files.reverse()
        for file in list_of_files:
            try:
                data = json.load(open(file, 'r'))
            except:
                continue

            key = data['key']
            if not key:
                continue
            result.append(key)

        seen = set()
        seen_add = seen.add
        result = [x for x in result if not (x in seen or seen_add(x))]

        return result

    @staticmethod
    def add_latest_used(key):
        """adds to the list"""
        if key in RecentKeys._blacklisted_items:
            return

        if key in RecentKeys._used_keys:
            RecentKeys._used_keys.remove(key)

        RecentKeys._used_keys = [key] + RecentKeys._used_keys


if __name__ == "__main__":
    import fire
    fire.Fire(RecentKeys)
