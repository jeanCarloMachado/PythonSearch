from __future__ import annotations

import logging
import re
from typing import List

from ddtrace import tracer
from grimoire.event_sourcing.message import MessageBroker
from grimoire.notification import send_notification

# @todo inject rather than import
from grimoire.search_run.entries.main import Configuration
from grimoire.string import generate_identifier

from search_run.context import Context
from search_run.interpreter.main import Interpreter


class Runner:
    """Responsible to execute the entries matched"""

    def __init__(self):
        self.message_broker = MessageBroker("search_runs_executed")

    @tracer.wrap("search_run.runner.run")
    def run(self, key: str, force_gui_mode=False, gui_mode=False, from_shortcut=False):
        """
        from_shortcut means that the key execution was triggered by a desktop shortcut
        """

        # if there are : in the line just take all before it as it is
        # usually the key from fzf, and our keys do not accept :
        if ":" in key:
            key = key.split(":")[0]
            # self.hide_launcher()

        if from_shortcut:
            send_notification(f"{key}")

        event = {"key": key, "from_shortcut": from_shortcut}
        self.message_broker.produce(event)

        matches = self._matching_keys(key)
        if force_gui_mode or gui_mode:
            Context.get_instance().enable_gui_mode()
        if len(matches) != 1:
            raise RunException.key_does_not_match(key, matches)

        return Interpreter.build_instance().default(matches[0])

    def hide_launcher(self):
        import os

        os.system("i3-msg '[title=launcher] move scratchpad'")

    def _matching_keys(self, key: str) -> List[str]:
        """
        give a key it will give suggestions that matches
        """

        key = generate_identifier(key)
        key_regex = re.compile(key)

        matching_keys = []
        for registered_key in Configuration().get_keys():
            encoded_registered_key = generate_identifier(registered_key)
            matches_kv_encoded = key_regex.search(encoded_registered_key)
            if matches_kv_encoded:
                logging.info(f"{key} matches {encoded_registered_key}")
                matching_keys.append(registered_key)

        return matching_keys


class RunException(Exception):
    @staticmethod
    def key_does_not_match(key: str, matches: List[str]):
        return RunException(
            f"Does pattern does not match 1 key ({key}) and ({matches})"
        )
