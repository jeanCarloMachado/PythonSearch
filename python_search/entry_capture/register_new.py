from __future__ import annotations

import datetime
import time
from typing import Tuple

from grimoire.event_sourcing.message import MessageBroker
from grimoire.string import emptish

from python_search.apps.clipboard import Clipboard
from python_search.entry_capture.data_capture_ui import AskQuestion
from python_search.entry_capture.entry_inserter import EntryInserter
from python_search.exceptions import RegisterNewException
from python_search.interpreter.base import BaseEntry
from python_search.interpreter.interpreter import Interpreter
from python_search.observability.logger import logging


class RegisterNew:
    """
    Responsible for registering new entries in your catalog
    """

    def __init__(self, configuration):
        self.configuration = configuration
        self.message_broker = MessageBroker("search_run_register_new")
        self.entry_inserter = EntryInserter(configuration)

    def from_clipboard(self):
        """
        Create a new inferred entry based on the clipboard content
        """
        clipboard_content, key = self._get_clipboard_content_and_ask_key(
            "New Entry Details"
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

        as_dict = {
            "snippet": content,
        }

        print(f"Dict: {as_dict}")

        self.entry_inserter.insert(key, as_dict)

    def german_from_text(self, key):
        """
        Register german workds you dont know by saving them to the clipboard and storing in python search
        """

        if emptish(key):
            raise RegisterNewException.empty_content()

        from python_search.interpreter.url import Url

        cmd = {
            "url": f"https://translate.google.com/?sl=de&tl=en&text={key}&op=translate"
        }
        Url(cmd).interpret_default()
        time.sleep(1)

        from python_search.apps.capture_input import CollectInput

        meaning = CollectInput().launch(f"Please type the meaning of ({key})")

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
        from python_search.entry_capture.data_capture_gui import \
            EntryCaptureGUI

        clipboard_content = self._get_clippboard_content()
        key, clipboard_content, _ = EntryCaptureGUI().launch(
            title, default_content=clipboard_content
        )

        return clipboard_content, key

    def _get_clippboard_content(self) -> str:
        clipboard_content = Clipboard().get_content()
        logging.info(f"Current clipboard content '{clipboard_content}'")
        if len(clipboard_content) == 0:
            raise RegisterNewException.empty_content()

        return clipboard_content


def transform_into_anonymous_entry(given_input: str) -> Tuple[str, dict]:
    now = datetime.datetime.now()
    key = f"no key {now.strftime('%Y %M %d %H %M %S')}"
    return key, {
        "snippet": given_input,
    }
