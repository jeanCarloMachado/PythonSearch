from __future__ import annotations

import re
import os
from typing import List
from datetime import datetime

from python_search.configuration.loader import ConfigurationLoader
from python_search.core_entities.core_entities import Key
from python_search.interpreter.cmd import CmdInterpreter, WRAP_IN_TERMINAL
from python_search.interpreter.interpreter_matcher import InterpreterMatcher
from python_search.logger import setup_run_key_logger
from python_search.error.exception import notify_exception
from python_search.search_ui.serialized_entry import (
    decode_serialized_data_from_entry_text,
)


class EntryRunner:
    """
    Responsible to execute the entries matched
    This class has to be optimized for performance so be mindful of imports.
    """

    def __init__(self, configuration = None):
        if not configuration:
            configuration = ConfigurationLoader().load_config()
        self._configuration = configuration
        self._logger = setup_run_key_logger()
        self._earliest_execution = datetime.now()

    @notify_exception()
    def run(
        self,
        entry_text: str,
        query_used: str = "",
        from_shortcut=False,
        wrap_in_terminal=False,
    ):
        """
        Runs an entry given its name or its partial name.

        Parameters:
            key: As it comes from FZF they is a str pair of key_name : {metadata}
            entry_rank_position: accounts for where the entry was when it was executed, if passed it will be used for
            from_shortcut means that the key execution was triggered by a desktop shortcut
        """

        key = str(Key.from_fzf(entry_text))
        if wrap_in_terminal:
            os.environ[WRAP_IN_TERMINAL] = "1"

        # if there are : in the line just take all before it as it is
        # usually the key from fzf, and our keys do not accept :

        metadata = decode_serialized_data_from_entry_text(entry_text, self._logger)
        rank_position = metadata.get("position")

        # when there are no matches we actually will use the query and interpret it
        if not key and query_used:
            CmdInterpreter({"cli_cmd": query_used}).interpret_default()
            return

        matches = self._matching_keys(key)

        if not matches:
            raise Exception(f"No key matches you given requested key: {key}")

        self._logger.info(
            f"""
            Matches of key: {key}
            matches: {matches}
            Query used: {query_used}
            Rank Position: {rank_position}
        """
        )


        if len(matches) > 1:
            key = min(matches, key=len)
            from python_search.apps.notification_ui import send_notification
            send_notification(
                f"Multiple matches for this key {matches} using the smaller"
            )

        result = InterpreterMatcher.build_instance(self._configuration).default(key)

        self._logger.info("Passed interpreter")
        from python_search.events.run_performed import EntryExecuted
        from python_search.events.run_performed.writer import LogRunPerformedClient

        run_performed = EntryExecuted(
            key=key,
            query_input=query_used,
            shortcut=from_shortcut,
            rank_uuid=metadata.get("uuid"),
            rank_position=metadata.get("position"),
            earliest_time=self._earliest_execution.isoformat(),
            after_execution_time=datetime.now().isoformat(),
        )
        LogRunPerformedClient(self._configuration).send(run_performed)

        return result

    def _matching_keys(self, key: str) -> List[str]:
        """
        give a key it will give suggestions that matches
        """

        key = generate_identifier(key)
        key_regex = re.compile(key)

        matching_keys = []
        for registered_key in self._configuration.get_keys():
            encoded_registered_key = generate_identifier(registered_key)
            matches_kv_encoded = key_regex.search(encoded_registered_key)
            if matches_kv_encoded:
                self._logger.info(f"{key} matches {encoded_registered_key}")
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
