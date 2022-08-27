from __future__ import annotations

import datetime
import time
from typing import Tuple

from grimoire.event_sourcing.message import MessageBroker
from grimoire.string import emptish

from python_search.apps.clipboard import Clipboard
from python_search.entry_capture.entry_inserter import EntryInserter
from python_search.entry_capture.gui import EntryCaptureGUI, EntryData
from python_search.exceptions import RegisterNewException
from python_search.interpreter.base import BaseInterpreter
from python_search.interpreter.interpreter_matcher import InterpreterMatcher


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
        entry_data: EntryData = EntryCaptureGUI().launch(
            "New Entry Details",
            default_content=Clipboard().get_content(),
            default_type="Snippet",
        )
        interpreter: BaseInterpreter = InterpreterMatcher.build_instance(
            self.configuration
        ).get_interpreter_from_type(entry_data.type)

        dict_entry = interpreter(entry_data.value).to_dict()
        if entry_data.tags:
            dict_entry['tags'] = entry_data.tags

        self.entry_inserter.insert(entry_data.key, dict_entry)

    def anonymous_snippet(self, content: str):
        """
        Create an anonymous snippet entry
        """

        if emptish(content):
            raise RegisterNewException.empty_content()

        key, as_dict = transform_into_anonymous_entry(content)
        self.entry_inserter.insert(key, as_dict)

    def german_from_text(self, key):
        """
        Register german workds you dont know by saving them to the clipboard and storing in python search
        """

        if emptish(key):
            raise RegisterNewException.empty_content()

        from python_search.interpreter.urlinterpreter import UrlInterpreter

        cmd = {
            "url": f"https://translate.google.com/?sl=de&tl=en&text={key}&op=translate"
        }
        UrlInterpreter(cmd).interpret_default()
        time.sleep(1)

        from python_search.apps.collect_input import CollectInput

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

        return entry_data.value, entry_data.key


def transform_into_anonymous_entry(given_input: str) -> Tuple[str, dict]:
    now = datetime.datetime.now()
    key = f"no key {now.strftime('%Y %M %d %H %M %S')}"
    return key, {
        "snippet": given_input,
    }
