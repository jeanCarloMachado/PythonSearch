from __future__ import annotations

import re
import os
from typing import List, Optional

from python_search.apps.notification_ui import send_notification
from python_search.configuration.configuration import PythonSearchConfiguration
from python_search.configuration.loader import ConfigurationLoader
from python_search.context import Context
from python_search.core_entities import Key
from python_search.events.run_performed import RunPerformed
from python_search.events.run_performed.writer import LogRunPerformedClient
from python_search.interpreter.cmd import CmdInterpreter
from python_search.interpreter.interpreter_matcher import InterpreterMatcher
from python_search.logger import setup_run_key_logger
from python_search.exceptions import notify_exception
from python_search.search_ui.serialized_entry import (
    decode_serialized_data_from_entry_text,
)


class EntryRunner:
    """
    Responsible to execute the _entries matched
    """

    def __init__(self, configuration: Optional[PythonSearchConfiguration] = None):
        if not configuration:
            configuration = ConfigurationLoader().load_config()
        self.configuration = configuration
        self.logger = setup_run_key_logger()

    @notify_exception()
    def run(
        self,
        entry_text: str,
        query_used: str = "",
        force_gui_mode=False,
        gui_mode=False,
        from_shortcut=False,
        fzf_pid_to_kill=None,
    ):
        """
        Runs an entry given its name or its partial name.

        Parameters:
            key: As it comes from FZF they is a str pair of key_name : {metadata}
            entry_rank_position: accounts for where the entry was when it was executed, if passed it will be used for
            from_shortcut means that the key execution was triggered by a desktop shortcut
        """

        key = str(Key.from_fzf(entry_text))

        self.logger.info("Arrived at run key")
        # if there are : in the line just take all before it as it is
        # usually the key from fzf, and our keys do not accept :

        if from_shortcut:
            send_notification(f"{key}")

        metadata = decode_serialized_data_from_entry_text(entry_text, self.logger)
        self.logger.info(f"Decoded metadata {metadata}")
        rank_position = metadata.get("position")

        # when there are no matches we actually will use the query and interpret it
        if not key and query_used:
            CmdInterpreter({"cli_cmd": query_used}).interpret_default()
            return

        matches = self._matching_keys(key)

        if not matches:
            raise Exception(f"No key matches you given requested key: {key}")

        self.logger.info(
            f"""
            Matches of key: {key}
            matches: {matches}
            Query used: {query_used}
            Rank Position: {rank_position}
        """
        )

        if force_gui_mode or gui_mode:
            Context.get_instance().enable_gui_mode()

        if len(matches) > 1:
            key = min(matches, key=len)
            send_notification(
                f"Multiple matches for this key {matches} using the smaller"
            )

        result = InterpreterMatcher.build_instance(self.configuration).default(key)

        self.logger.info("Passed interpreter")
        run_performed = RunPerformed(
            key=key,
            query_input=query_used,
            shortcut=from_shortcut,
            rank_uuid=metadata.get("uuid"),
            rank_position=metadata.get("position"),
        )
        self.logger.info(f"Run performed = {run_performed}")
        LogRunPerformedClient().send(run_performed)

        # this needs to be last as it will kill the process
        if fzf_pid_to_kill:
            print("Killing fzf")
            os.system(f"kill -9 {fzf_pid_to_kill}")

        return result

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
                self.logger.info(f"{key} matches {encoded_registered_key}")
                matching_keys.append(registered_key)

        return matching_keys


def generate_identifier(string):
    """
    strip the string from all special characters lefting only [A-B-09]
    """
    result = "".join(e for e in string if e.isalnum())
    result = result.lower()

    return result


def main():
    """
    Entry point to run a key
    """
    import fire

    fire.Fire(EntryRunner().run)
