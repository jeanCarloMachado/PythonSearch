from __future__ import annotations


from python_search.configuration.loader import ConfigurationLoader
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

    def launch_ui(self):
        from declarative_ui import UIBuilder
        from python_search.apps.clipboard import Clipboard

        clipboard_content = Clipboard().get_content()
        default_type = "snippet"
        if clipboard_content.startswith("http"):
            default_type = "url"
        result = UIBuilder().build(
            [
                {"key": "key", "type": "input"},
                {"key": "value", "type": "text", "value": clipboard_content},
                {
                    "key": "type",
                    "type": "select",
                    "value": default_type,
                    "values": ["snippet", "cli_cmd", "cmd", "url", "file"],
                },
            ],
            title="Register New Entry",
        )

        self.register(key=result["key"], value=result["value"], type=result["type"])

    @notify_exception()
    def register(self, *, key: str, value: str, type: str):
        """
        The non ui driven registering api
        Args:
            key:
            value:
            tag:

        Returns:

        """
        key = self._sanitize_key(key)

        if not type:
            interpreter: BaseInterpreter = InterpreterMatcher.build_instance(
                self.configuration
            ).get_interpreter(value)
            dict_entry = interpreter.to_dict()
        else:
            if type == "snippet":
                dict_entry = {"snippet": value}
            elif type == "cli_cmd":
                dict_entry = {"cli_cmd": value}
            elif type == "cmd":
                dict_entry = {"cmd": value}
            elif type == "url":
                dict_entry = {"url": value}
            elif type == "file":
                dict_entry = {"file": value}
            else:
                raise Exception(f"Unknown type {type}")

        self.entry_inserter.insert(key, dict_entry)

    def from_stdin_as_json(self):
        import sys
        import json

        data = json.load(sys.stdin)
        key = data["key"]
        value = data["value"]
        type = data["type"]
        self.register(key=key, value=value, type=type)

    def _sanitize_key(self, key):
        return key.replace("\n", " ").replace(":", " ").strip()


def main():
    import fire

    fire.Fire(RegisterNew)
