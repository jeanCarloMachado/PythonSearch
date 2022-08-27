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
from python_search.interpreter.file import FileInterpreter
from python_search.interpreter.interpreter_matcher import InterpreterMatcher
from python_search.interpreter.url import UrlInterpreter


class RegisterNew:
    """
    Responsible for registering new entries in your catalog
    """

    def __init__(self, configuration):
        self.configuration = configuration
        self.message_broker = MessageBroker("search_run_register_new")
        self.entry_inserter = EntryInserter(configuration)

    def launch_ui(self, default_type=None, default_key=None, default_content=None):
        """
        Create a new inferred entry based on the clipboard content
        """

        if not default_content:
            default_content = Clipboard().get_content()

        if not default_type:
            default_type = self._infer_default_type(default_content)

        entry_data: EntryData = EntryCaptureGUI().launch(
            "New Entry Details",
            default_content=default_content,
            default_key=default_key,
            default_type=default_type,
        )
        interpreter: BaseInterpreter = InterpreterMatcher.build_instance(
            self.configuration
        ).get_interpreter_from_type(entry_data.type)

        dict_entry = interpreter(entry_data.value).to_dict()
        if entry_data.tags:
            dict_entry["tags"] = entry_data.tags

        self.entry_inserter.insert(entry_data.key, dict_entry)

    def _infer_default_type(self, content):
        if UrlInterpreter.is_url(content):
            return "Url"

        if FileInterpreter.file_exists(content):
            return "File"

        return "Cmd"

    def anonymous_snippet(self):
        """
        Create an anonymous snippet entry
        """

        now = datetime.datetime.now()
        key = f"no key {now.strftime('%Y %M %d %H %M %S')}"

        self.launch_ui(default_key=key, default_type="Snippet")

    def german_from_text(self, key):
        """
        Register german workds you dont know by saving them to the clipboard and storing in python search
        """

        if emptish(key):
            raise RegisterNewException.empty_content()

        from python_search.interpreter.url import UrlInterpreter

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
