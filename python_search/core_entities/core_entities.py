"""

Core entities reused in the hole project.
They should be side-effect free

"""
from __future__ import annotations

from typing import List, Optional

from numpy import ndarray


class Key:
    """Represents a key of an entry"""

    def __init__(self, key):
        self.key = key

    @staticmethod
    def from_fzf(entry_text: str) -> Key:
        key = entry_text.split(":")[0] if ":" in entry_text else entry_text
        key = key.strip()
        return Key(key)

    def __str__(self):
        return self.key


class Entry:
    """
    An python dictionary we write in PythonSearch
    """

    key: str
    value: Optional[dict]

    def __init__(self, key: str = None, value: dict = None):
        """
        :param name: the name of the entry
        :param value: the value of the entry
        """
        self.key = key
        self.value = value

    def get_only_content(self):
        if "url" in self.value:
            return self.value.get("url")

        if "file" in self.value:
            return self.value.get("file")

        if "snippet" in self.value:
            return self.value.get("snippet")

        if "cli_cmd" in self.value or "cmd" in self.value:
            return self.value.get("cli_cmd", self.value.get("cmd"))

        if "callable" in self.value:
            value = self.value.get("callable")
            import dill

            return dill.source.getsource(value)
