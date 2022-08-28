from __future__ import annotations

import json
import re
from typing import List

from python_search.apps.notification_ui import send_notification
from python_search.config import PythonSearchConfiguration
from python_search.context import Context
from python_search.events.producer import EventProducer
from python_search.interpreter.cmd import CmdInterpreter
from python_search.interpreter.interpreter_matcher import InterpreterMatcher
from python_search.observability.logger import (initialize_systemd_logging,
                                                logging)


class EntryRunner:
    """
    Responsible to execute the entries matched
    """

    def __init__(self, configuration: PythonSearchConfiguration):
        self.configuration = configuration
        self.logging = initialize_systemd_logging()

    def run(
        self,
        key: str,
        query_used: str = "",
        force_gui_mode=False,
        gui_mode=False,
        from_shortcut=False,
    ):
        """
        Runs an entry given its name or its partial name.

        Parameters:
            key: As it comes from FZF they is a str pair of key_name : {metadata}
            entry_rank_position: accounts for where the entry was when it was executed, if passed it will be used for
            from_shortcut means that the key execution was triggered by a desktop shortcut
        """

        # if there are : in the line just take all before it as it is
        # usually the key from fzf, and our keys do not accept :
        metadata = ""
        if ":" in key:
            key, metadata = key.split(":", 1)
            self.logging.info(f"metadata: {metadata}")

        if from_shortcut:
            send_notification(f"{key}")

        rank_position = None

        if metadata:
            try:
                matadata_dict = json.loads(metadata)
                rank_position = matadata_dict.get("position")
            except BaseException as e:
                self.logging.warning(f"Could not decode metadata: {e}")

        # when there are no matches we actually will use the query and interpret it
        if not key and query_used:
            CmdInterpreter({"cli_cmd": query_used}).interpret_default()
            return

        matches = self._matching_keys(key)

        if not matches:
            raise Exception(f"No key matches you given requested key: {key}")

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

        if self.configuration.supported_features.is_enabled("event_tracking"):
            logging.info("Starting event recording procedure")
            from python_search.events.events import SearchRunPerformed

            EventProducer().send_object(
                SearchRunPerformed(
                    key=key, query_input=query_used, shortcut=from_shortcut
                )
            )

        real_key: str = matches[0]

        if len(matches) > 1:
            real_key = min(matches, key=len)
            send_notification(
                f"Multiple matches for this key {matches} using the smaller"
            )

        return InterpreterMatcher.build_instance(self.configuration).default(real_key)

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


def generate_identifier(string):
    """
    strip the string from all special characters lefting only [A-B-09]
    """
    result = "".join(e for e in string if e.isalnum())
    result = result.lower()

    return result
