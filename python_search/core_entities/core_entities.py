"""

Core entities reused in the hole project.
They should be side-effect free

"""
from __future__ import annotations

from typing import Optional, Literal


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

    def get_content_str(self, strip_new_lines=False) -> str:
        if not self.value:
            return ""
        if type(self.value) == str:
            result = self.value
            return result

        if "url" in self.value:
            result = self.value.get("url")

        if "file" in self.value:
            result = self.value.get("file")

        if "snippet" in self.value:
            result = self.value.get("snippet")

        if "cli_cmd" in self.value or "cmd" in self.value:
            result = self.value.get("cli_cmd", self.value.get("cmd"))

        if "callable" in self.value:
            value = self.value.get("callable")
            import dill

            result = dill.source.getsource(value)
        result = str(result)

        if strip_new_lines:
            result = result.replace("\n", " ")

        return result

    def get_type_str(self) -> Literal["url", "file", "snippet", "cli_cmd", "callable"]:
        if not self.value:
            return "snippet"

        if "url" in self.value:
            return "url"

        if "file" in self.value:
            return "file"

        if "snippet" in self.value:
            return "snippet"

        if "cli_cmd" in self.value or "cmd" in self.value:
            return "cli_cmd"

        if "callable" in self.value:
            return "callable"

        return "snippet"
