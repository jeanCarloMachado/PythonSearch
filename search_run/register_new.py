from __future__ import annotations

from typing import Tuple

from pydantic import BaseModel

from grimoire import s
from grimoire.desktop.clipboard import Clipboard
from grimoire.event_sourcing.message import MessageBroker
from grimoire.file import Replace
from grimoire.notification import send_notification
from search_run.config import MAIN_FILE
from grimoire.ask_question import AskQuestion
from search_run.interpreter.base import BaseInterpreter
from search_run.interpreter.main import Interpreter

from grimoire.string import emptish, quote_with, remove_new_lines, remove_special_chars


class RegisterNew:
    """
    Responsible for registering new entries in search run
    """

    def __init__(self):
        self.message_broker = MessageBroker("search_run_register_new")

    def infer_from_clipboard(self):
        """
        Create a new inferred entry based on the clipboard content
        """
        clipboard_content, key = self._get_user_provided_data("Name your content")

        clipboard_content = remove_new_lines(clipboard_content)
        clipboard_content = quote_with(clipboard_content, '"')

        interpreter: BaseInterpreter = Interpreter.build_instance().get_interpreter(
            clipboard_content
        )
        serialized = interpreter.serialize()
        serialized = remove_new_lines(serialized)

        Replace().append_after_placeholder(
            MAIN_FILE, "# NEW_COMMANDS_HERE", f"        '{key}': {serialized},"
        )
        s.run("search_run export_configuration")

    def snippet_from_clipboard(self):
        """
        Create a search run snippet entry based on the clipboard content
        """
        snippet_content, key = self._get_user_provided_data("Name your snippet")
        if emptish(snippet_content):
            raise RegisterNewException.empty_content()
        snippet_content = snippet_content.replace("\n", " ")
        snippet_content = remove_special_chars(snippet_content, ALLOWED_SPECIAL_CHARS)

        snippet_content = f"'''{snippet_content}'''"
        row_entry = "{'snippet': " + snippet_content + "},"
        line_to_add = f"        '{key}': {row_entry}"
        Replace().append_after_placeholder(
            MAIN_FILE, "# NEW_COMMANDS_HERE", line_to_add
        )
        s.run("search_run export_configuration")

    def _get_user_provided_data(self, title) -> Tuple[ClipboardContent, EntryKey]:
        clipboard_content = Clipboard().get_content()
        if emptish(clipboard_content):
            raise RegisterNewException.empty_content()

        send_notification(f"Content to store: {clipboard_content}")
        key = AskQuestion().ask(title)

        event = RegisterExecuted(**{"key": key, "content": clipboard_content})
        self.message_broker.produce(event.dict())

        return clipboard_content, key


class RegisterExecuted(BaseModel):
    key: str
    content: str


ClipboardContent = str
EntryKey = str
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


class RegisterNewException(Exception):
    config = {
        "disable_tray_message": True,
        "enable_notification": True,
        "disable_sentry": True,
    }

    @staticmethod
    def empty_content():
        return RegisterNewException(f"Will not register as content looks too small")
