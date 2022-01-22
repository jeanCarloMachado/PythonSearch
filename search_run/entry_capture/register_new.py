from __future__ import annotations

import datetime
from typing import Tuple

from grimoire.desktop.clipboard import Clipboard
from grimoire.event_sourcing.message import MessageBroker
from grimoire.file import Replace
from grimoire.notification import send_notification
from grimoire.string import (emptish, quote_with, remove_new_lines,
                             remove_special_chars)

from search_run.apps.terminal import Terminal
from search_run.base_configuration import EntriesGroup
from search_run.entry_capture.data_capture_ui import AskQuestion
from search_run.events.events import RegisterExecuted
from search_run.exceptions import RegisterNewException
from search_run.interpreter.base import BaseInterpreter
from search_run.interpreter.main import Interpreter
from search_run.observability.logger import logging


class RegisterNew:
    """
    Responsible for registering new entries in your catalog
    """

    def __init__(self, configuration: EntriesGroup):
        self.message_broker = MessageBroker("search_run_register_new")
        self.configuration = configuration

    def infer_from_clipboard(self):
        """
        Create a new inferred entry based on the clipboard content
        """
        clipboard_content, key = self._get_user_provided_data("Name your entry")

        clipboard_content = remove_new_lines(clipboard_content)
        clipboard_content = quote_with(clipboard_content, '"')

        interpreter: BaseInterpreter = Interpreter.build_instance(
            self.configuration
        ).get_interpreter(clipboard_content)
        as_dict = interpreter.to_dict()
        as_dict["created_at"] = datetime.datetime.now().isoformat()

        serialized = str(as_dict)
        serialized = remove_new_lines(serialized)

        Replace().append_after_placeholder(
            self.configuration.get_source_file(),
            "# NEW_COMMANDS_HERE",
            f"        '{key}': {serialized},",
        )
        Terminal.run_command("search_run export_configuration")

    def snippet_from_clipboard(self):
        """
        Create a search run snippet entry based on the clipboard content
        """
        snippet_content, key = self._get_user_provided_data("Name your string snippet")
        if emptish(snippet_content):
            raise RegisterNewException.empty_content()

        snippet_content = snippet_content.replace("\n", " ")
        snippet_content = remove_special_chars(snippet_content, ALLOWED_SPECIAL_CHARS)

        as_dict = {
            "snippet": snippet_content,
            "created_at": datetime.datetime.now().isoformat(),
        }

        row_entry = str(as_dict)
        line_to_add = f"        '{key}': {row_entry},"
        Replace().append_after_placeholder(
            self.configuration.get_source_file(), "# NEW_COMMANDS_HERE", line_to_add
        )
        Terminal.run_command("search_run export_configuration")

    def _get_user_provided_data(self, title) -> Tuple[str, str]:
        clipboard_content = Clipboard().get_content()
        logging.info(f"Current clipboard content '{clipboard_content}'")
        if emptish(clipboard_content):
            raise RegisterNewException.empty_content()

        send_notification(f"Content to store: {clipboard_content}")
        key = AskQuestion().ask(title)

        event = RegisterExecuted(**{"key": key, "content": clipboard_content})
        self.message_broker.produce(event.dict())

        return clipboard_content, key


ALLOWED_SPECIAL_CHARS = [
    "@",
    "-",
    "_",
    "'",
    "?",
    "=",
    ",",
    ".",
    " ",
    "/",
    "(",
    ")",
    ";",
    '"',
    "%",
    " ",
    ":",
    "{",
    "'",
    '"',
    "}",
    "?",
]
