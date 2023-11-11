from __future__ import annotations

from typing import Optional

from python_search.configuration.loader import ConfigurationLoader
from python_search.core_entities.core_entities import Key, Entry
from python_search.entry_capture.filesystem_entry_inserter import (
    FilesystemEntryInserter,
)

from python_search.interpreter.base import BaseInterpreter
from python_search.interpreter.interpreter_matcher import InterpreterMatcher
from python_search.error.exception import notify_exception


class RegisterNew:
    """
    Entry point for the registering of new entries
    """

    def __init__(self, configuration=None):
        if not configuration:
            configuration = ConfigurationLoader().load_config()

        self.configuration = configuration
        self.entry_inserter = FilesystemEntryInserter(configuration)


    @notify_exception()
    def register(self, *, key: str, value: str, tag: Optional[str] = None):
        """
        The non ui driven registering api
        Args:
            key:
            value:
            tag:

        Returns:

        """
        print(f"Registering new entry with tag = {tag}")
        key = self._sanitize_key(key)

        interpreter: BaseInterpreter = InterpreterMatcher.build_instance(
            self.configuration
        ).get_interpreter(value)
        dict_entry = interpreter.to_dict()
        if tag:
            dict_entry["tags"] = [tag]

        self.entry_inserter.insert(key, dict_entry)

    def from_stdin_as_json(self):
        import sys
        import json

        data = json.load(sys.stdin)
        key = data["key"]
        value = data["value"]
        tag = data.get("tag", None)
        self.register(key=key, value=value, tag=tag)


    def _sanitize_key(self, key):
        return key.replace("\n", " ").replace(":", " ").strip()


def main():
    import fire

    fire.Fire(RegisterNew)



