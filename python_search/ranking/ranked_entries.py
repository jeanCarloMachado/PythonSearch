from __future__ import annotations

from typing import List, Tuple


class RankedEntries:
    type = List[Tuple[str, dict]]

    @staticmethod
    def get_list_of_tuples(from_keys: List[str], entities: dict) -> RankedEntries.type:
        used_entries = []
        for used_key in from_keys:
            if used_key not in entities:
                continue
            used_entries.append((used_key, entities[used_key]))
        return used_entries
