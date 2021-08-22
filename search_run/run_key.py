from __future__ import annotations

import logging
import re
from typing import List

from ddtrace import tracer

from grimoire.databases.redis import get_redis
from grimoire.event_sourcing.message import MessageBroker
from grimoire.notification import send_notification
from search_run.context import Context
from search_run.interpreter.main import Interpreter

from grimoire.search_run.search_run_config import Configuration
from grimoire.string import generate_identifier
from grimoire.time import Date, date_from_str, is_today


class RunKey:
    def __init__(self):
        self.message_broker = MessageBroker("search_runs_executed")

    @tracer.wrap("run_key_entire_process")
    def run(self, key: Key, force_gui_mode=False, gui_mode=False, from_shortcut=False):
        """
        from_shortcut means that the key execution was triggered by a desktop shortcut
        """
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

    def _matching_keys(self, key: Key) -> List[Key]:
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


Key = str


class DailyGmailUsageCounter:
    def __init__(self):
        self.redis = get_redis()

    def listen(self, event):
        previous_str: str = self.redis.hget(
            f"search_run_statistics", "daily_gmail_usage"
        )
        previous: int = 0 if not previous_str else int(previous_str)

        latest_usage_str = self.redis.hget(
            f"search_run_statistics", "latest_gmail_usage"
        )
        latest_usage = date_from_str(latest_usage_str)
        if not is_today(latest_usage):
            previous = 0

        if event["key"] != "gmailclient":
            return

        new_value = previous + 1
        self.redis.hset(f"search_run_statistics", "daily_gmail_usage", new_value)
        self.redis.hset(f"search_run_statistics", "latest_gmail_usage", Date.now_str())

    def get_daily_total(self) -> int:
        result = int(self.redis.hget(f"search_run_statistics", "daily_gmail_usage"))
        return result


class RunException(Exception):
    @staticmethod
    def key_does_not_match(key: Key, matches: List[Key]):
        return RunException(
            f"Does pattern does not match 1 key ({key}) and ({matches})"
        )
