from __future__ import annotations

from typing import Optional

from python_search.configuration.loader import ConfigurationLoader
from python_search.core_entities.core_entities import Key, Entry
from python_search.entry_capture.filesystem_entry_inserter import (
    FilesystemEntryInserter,
)

from python_search.entry_type.entity import infer_default_type
from python_search.exceptions import RegisterNewException
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

    def _sanitize_key(self, key):
        return key.replace("\n", " ").replace(":", " ").strip()

    def launch_from_fzf(self, key_expression):
        import json

        key = str(Key.from_fzf(key_expression))
        key_len = len(key_expression.split(":")[0])
        body = key_expression[key_len + 1 :]
        body = json.loads(body.strip())
        content = Entry(key, body).get_content_str()

        self.launch_ui(default_key=key, default_content=content)

    @notify_exception()
    def launch_ui(self, default_type=None, default_key="", default_content=""):
        """
        Create a new inferred entry based on the clipboard content
        """
        if not default_content:
            from python_search.apps.clipboard import Clipboard
            default_content = Clipboard().get_content()

        if not default_type:
            default_type = infer_default_type(default_content)

        from python_search.entry_capture.entry_inserter_gui.entry_inserter_gui import (
            NewEntryGUI,
            GuiEntryData,
        )
        entry_data: GuiEntryData = NewEntryGUI().launch(
            "New Entry",
            default_content=default_content,
            default_key=default_key,
            default_type=default_type,
        )
        self.save_entry_data(entry_data)

    def save_entry_data(self, entry_data):
        key = self._sanitize_key(entry_data.key)
        interpreter: BaseInterpreter = InterpreterMatcher.build_instance(
            self.configuration
        ).get_interpreter_from_type(entry_data.type)

        dict_entry = interpreter(entry_data.value).to_dict()
        if entry_data.tags:
            dict_entry["tags"] = entry_data.tags

        self.entry_inserter.insert(key, dict_entry)



def main():
    import fire

    fire.Fire(RegisterNew)


def launch_ui():

    RegisterNew().launch_ui()

