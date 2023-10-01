from __future__ import annotations

from typing import List


class GuiEntryData:
    """
    Entry _entries schema

    """

    key: str
    value: str
    type: str
    tags: List[str]

    def __init__(self, key, value, type, tags):
        if not key:
            raise Exception("Key is required")

        if not value:
            raise Exception("Value is required")

        self.key = key
        self.value = value
        self.type = type
        self.tags = tags
