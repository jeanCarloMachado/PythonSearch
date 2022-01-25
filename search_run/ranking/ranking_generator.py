from __future__ import annotations

import json
from collections import namedtuple
from typing import List, Tuple

from search_run.base_configuration import PythonSearchConfiguration
from search_run.events.latest_used_entries import LatestUsedEntries
from search_run.observability.logger import logging


class RankingGenerator:
    """
    Write to the file all the commands and generates shortcuts
    """

    ModelInfo = namedtuple("ModelInfo", "features label")
    model_info = ModelInfo(["position", "key_lenght"], "input_lenght")

    def __init__(self, configuration: PythonSearchConfiguration):
        self.configuration = configuration

    def generate(self):
        """
        Recomputes the rank and saves the results on the file to be read
        """

        entries: dict = self.load_entries()
        result = []
        used_entries = []

        if self.configuration.supported_features.is_enabled("redis"):
            latest_used = LatestUsedEntries().get_latest_used_keys()
            for used_key in latest_used:
                if used_key not in entries or used_key in used_entries:
                    continue
                used_entries.append((used_key, entries[used_key]))
                del entries[used_key]
            # reverse the list given that we pop from the end
            used_entries.reverse()

        increment = 1
        for key in entries.keys():
            increment += 1
            if increment % 2 == 0 and len(used_entries):
                used_entry = used_entries.pop()
                logging.debug(f"Increment: {increment}  with entry {used_entry}")
                result.append(used_entry)

            result.append((key, entries[key]))

        return self._export_to_file(result)

    def load_entries(self):
        """ Loads the current state of the art of search run entries"""
        return self.configuration.commands

    def _export_to_file(self, data: List[Tuple[str, dict]]):
        position = 1
        for name, content in data:
            try:
                content["key_name"] = name
                content["rank_position"] = position
                content_str = json.dumps(content, default=tuple, ensure_ascii=True)
            except BaseException:
                content = content
                content_str = str(content)

            position = position + 1

            content_str = f"{name.lower()}: " + content_str
            content_str = content_str.replace("\\", "\\\\")
            print(content_str)
