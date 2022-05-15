from __future__ import annotations

import re
from typing import List

from grimoire.notification import notify_send, send_notification
from grimoire.string import generate_identifier

from search_run.config import PythonSearchConfiguration
from search_run.context import Context
from search_run.events.events import SearchRunPerformed
from search_run.events.producer import EventProducer
from search_run.exceptions import RunException
from search_run.interpreter.interpreter import Interpreter
from search_run.observability.logger import initialize_systemd_logging, logging


class EntryRunner:
    """
    Responsible to execute the entries matched
    """

    def __init__(self, configuration: PythonSearchConfiguration):
        self.configuration = configuration
        self.logging = initialize_systemd_logging()

    def run_key(
        self,
        key: str,
        query_used: str = "",
        force_gui_mode=False,
        gui_mode=False,
        from_shortcut=False,
        rank_position=None,
    ):
        """
        from_shortcut means that the key execution was triggered by a desktop shortcut

        Parameters
            entry_rank_position: accounts for where the entry was when it was executed, if passed it will be used for
            tracking
        """

        # if there are : in the line just take all before it as it is
        # usually the key from fzf, and our keys do not accept :
        if ":" in key:
            key = key.split(":")[0]

        if from_shortcut:
            send_notification(f"{key}")

        matches = self._matching_keys(key)

        self.logging.info(
            f"""
            Matches of key: {key}
            matches: {matches}
            Query used: {query_used}
            Rank Position: {rank_position}
        """
        )

        if force_gui_mode or gui_mode:
            Context.get_instance().enable_gui_mode()

        if not matches:
            raise RunException.key_does_not_exist(key)

        real_key: str = matches[0]
        if len(matches) > 1:
            real_key = min(matches, key=len)
            notify_send(f"Multiple matches for this key {matches} using the smaller")

        if self.configuration.supported_features.is_enabled("event_tracking"):
            EventProducer().send_object(
                SearchRunPerformed(
                    key=key, query_input=query_used, shortcut=from_shortcut
                )
            )

        return Interpreter.build_instance(self.configuration).default(real_key)

    def _matching_keys(self, key: str) -> List[str]:
        """
        give a key it will give suggestions that matches
        """

        key = generate_identifier(key)
        key_regex = re.compile(key)

        matching_keys = []
        for registered_key in self.configuration.get_keys():
            encoded_registered_key = generate_identifier(registered_key)
            matches_kv_encoded = key_regex.search(encoded_registered_key)
            if matches_kv_encoded:
                logging.info(f"{key} matches {encoded_registered_key}")
                matching_keys.append(registered_key)

        return matching_keys
