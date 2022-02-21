from __future__ import annotations

import datetime
from typing import Tuple

from grimoire.desktop.clipboard import Clipboard
from grimoire.event_sourcing.message import MessageBroker
from grimoire.notification import send_notification
from grimoire.string import (emptish, quote_with, remove_new_lines,
                             remove_special_chars)
from grimoire.translator.translator import Translator

from search_run.entry_capture.data_capture_ui import AskQuestion
from search_run.entry_capture.entry_inserter import EntryInserter
from search_run.events.events import RegisterExecuted
from search_run.exceptions import RegisterNewException
from search_run.interpreter.base import BaseInterpreter
from search_run.interpreter.main import Interpreter
from search_run.observability.logger import logging


class RegisterNew:
    """
    Responsible for registering new entries in your catalog
    """

    def __init__(self, configuration: PythonSearchConfiguration):
        self.configuration = configuration
        self.message_broker = MessageBroker("search_run_register_new")
        self.entry_inserter = EntryInserter(configuration)

    def infer_from_clipboard(self):
        """
        Create a new inferred entry based on the clipboard content
        """
        clipboard_content, key = self._get_user_provided_data("Name your entry")

        clipboard_content = self._sanitize(clipboard_content)

        interpreter: BaseInterpreter = Interpreter.build_instance(
            self.configuration
        ).get_interpreter(clipboard_content)

        as_dict = interpreter.to_dict()
        as_dict["created_at"] = datetime.datetime.now().isoformat()

        self.entry_inserter.insert(key, as_dict)

    def _sanitize(self, content):
        """
        Cleans all system inputs to be stored as dictionaries
        """
        content = content.replace("\n", " ")
        content = content.replace("'", '"')
        content = remove_special_chars(content, EntryInserter.ALLOWED_SPECIAL_CHARS)

        return content

    def snippet_from_clipboard(self):
        """
        Create a snippet entry based on the clipboard content
        """
        snippet_content, key = self._get_user_provided_data("Name your string snippet")
        if emptish(snippet_content):
            raise RegisterNewException.empty_content()

        snippet_content = self._sanitize(snippet_content)

        as_dict = {
            "snippet": snippet_content,
            "created_at": datetime.datetime.now().isoformat(),
        }

        self.entry_inserter.insert(key, as_dict)

    def german_from_clipboard(self):
        """ Register german workds you dont know by saving them to the clipboard and storing in python search """
        key = Clipboard().get_content()

        if emptish(key):
            raise RegisterNewException.empty_content()

        Translator().translator_clipboard()
        import time

        time.sleep(1)

        meaning = AskQuestion().ask(f"Please type the meaning of ({key})")

        if emptish(meaning):
            raise RegisterNewException.empty_content()

        meaning = self._sanitize(meaning)

        as_dict = {
            "snippet": meaning,
            "language": "German",
            "created_at": datetime.datetime.now().isoformat(),
        }

        self.entry_inserter.insert(key, as_dict)

    def _get_user_provided_data(self, title) -> Tuple[str, str]:
        clipboard_content = Clipboard().get_content()
        logging.info(f"Current clipboard content '{clipboard_content}'")
        if emptish(clipboard_content):
            raise RegisterNewException.empty_content()

        send_notification(f"Content to store: {clipboard_content}")
        key = AskQuestion().ask(title)

        if self.configuration.supported_features.is_enabled("event_tracking"):
            event = RegisterExecuted(**{"key": key, "content": clipboard_content})
            self.message_broker.produce(event.dict())

        return clipboard_content, key
