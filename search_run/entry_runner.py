from __future__ import annotations

import logging
import re
from typing import List

# @todo inject rather than import
from grimoire.notification import notify_send, send_notification
from grimoire.string import generate_identifier

from search_run.context import Context
from search_run.events.events import SearchRunPerformed
from search_run.events.producer import EventProducer
from search_run.exceptions import RunException
from search_run.interpreter.main import Interpreter


class Runner:
    """Responsible to execute the entries matched"""

    def __init__(self, configuration):
        self.configuration = configuration
        self.event_producer = EventProducer()

    def run(
        self,
        key: str,
        force_gui_mode=False,
        gui_mode=False,
        from_shortcut=False,
        query_used: str = "",
    ):
        """
        from_shortcut means that the key execution was triggered by a desktop shortcut
        """

        # if there are : in the line just take all before it as it is
        # usually the key from fzf, and our keys do not accept :
        if ":" in key:
            key = key.split(":")[0]

        if from_shortcut:
            send_notification(f"{key}")

        matches = self._matching_keys(key)
        if force_gui_mode or gui_mode:
            Context.get_instance().enable_gui_mode()

        if not matches:
            raise RunException.key_does_not_exist(key)

        real_key: str = matches[0]
        if len(matches) > 1:
            real_key = min(matches, key=len)
            notify_send(f"Multiple matches for this key {matches} using the maller")

        self.event_producer.send_object(
            SearchRunPerformed(key=key, query_input=query_used, shortcut=from_shortcut)
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