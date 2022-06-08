from __future__ import annotations

import datetime
import time
from typing import Tuple

from search_run.apps.clipboard import Clipboard
from grimoire.event_sourcing.message import MessageBroker
from search_run.apps.notification_ui import send_notification
from grimoire.string import emptish

from search_run.entry_capture.data_capture_ui import AskQuestion
from search_run.entry_capture.entry_inserter import EntryInserter
from search_run.exceptions import RegisterNewException
from search_run.interpreter.base import BaseEntry
from search_run.interpreter.interpreter import Interpreter
from search_run.observability.logger import logging


class RegisterNew:
    """
    Responsible for registering new entries in your catalog
    """

    def __init__(self, configuration):
        self.configuration = configuration
        self.message_broker = MessageBroker("search_run_register_new")
        self.entry_inserter = EntryInserter(configuration)

    def infer_from_clipboard(self):
        """
        Create a new inferred entry based on the clipboard content
        """
        clipboard_content, key = self._get_clipboard_content_and_ask_key(
            "Name your entry"
        )
        self.infer_content(clipboard_content, key)

    def infer_content(self, content: str, key: str):
        """Add an entry inferring the type"""
        interpreter: BaseEntry = Interpreter.build_instance(
            self.configuration
        ).get_interpreter(content)

        as_dict = interpreter.to_dict()

        self.entry_inserter.insert(key, as_dict)

    def anonymous_snippet(self, content: str):
        """
        Create an anonymous snippet entry
        """

        if emptish(content):
            raise RegisterNewException.empty_content()

        key, as_dict = transform_into_anonymous_entry(content)
        self.entry_inserter.insert(key, as_dict)

    def snippet_from_clipboard(self):
        """
        Create a snippet entry based on the clipboard content
        """
        snippet_content, key = self._get_clipboard_content_and_ask_key(
            "Name your string snippet"
        )

        self.register_snippet(snippet_content, key)

    def register_snippet(self, content, key):
        if emptish(content):
            raise RegisterNewException.empty_content()

        as_dict = {
            "snippet": content,
        }

        print(f"Dict: {as_dict}")

        self.entry_inserter.insert(key, as_dict)

    def german_from_clipboard(self):
        """Register german workds you dont know by saving them to the clipboard and storing in python search"""
        key = Clipboard().get_content()

        if emptish(key):
            raise RegisterNewException.empty_content()

        from grimoire.translator.translator import Translator
        Translator().translator_clipboard()
        time.sleep(1)

        meaning = AskQuestion().ask(f"Please type the meaning of ({key})")

        if emptish(meaning):
            raise RegisterNewException.empty_content()

        as_dict = {
            "snippet": meaning,
            "language": "German",
        }

        self.entry_inserter.insert(key, as_dict)

    def _get_clipboard_content_and_ask_key(self, title) -> Tuple[str, str]:
        """
        @todo find a better name here
        Get content from clipboard and from input
        AND produces the event
        """

        clipboard_content = self._get_clippboard_content()
        send_notification(f"Content to store: {clipboard_content}")
        key = AskQuestion().ask(title)

        if self.configuration.supported_features.is_enabled("event_tracking"):
            from search_run.events.events import RegisterExecuted
            event = RegisterExecuted(**{"key": key, "content": clipboard_content})
            self.message_broker.produce(event.dict())

        return clipboard_content, key

    def _get_clippboard_content(self) -> str:
        clipboard_content = Clipboard().get_content()
        logging.info(f"Current clipboard content '{clipboard_content}'")
        if emptish(clipboard_content):
            raise RegisterNewException.empty_content()

        return clipboard_content


def transform_into_anonymous_entry(given_input: str) -> Tuple[str, dict]:
    now = datetime.datetime.now()
    key = f"no key {now.strftime('%Y %M %d %H %M %S')}"
    return key, {
        "snippet": given_input,
    }
