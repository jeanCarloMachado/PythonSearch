from __future__ import annotations

import json
from collections import namedtuple
from typing import List, Tuple

from search_run.acronyms import generate_acronyms
from search_run.base_configuration import PythonSearchConfiguration
from search_run.observability.logger import initialize_systemd_logging, logging


class RankingGenerator:
    """
    Write to the file all the commands and generates shortcuts
    """

    ModelInfo = namedtuple("ModelInfo", "features label")
    model_info = ModelInfo(["position", "key_lenght"], "input_lenght")

    def __init__(self, configuration: PythonSearchConfiguration):
        initialize_systemd_logging()
        self.configuration = configuration

    def generate(self):
        """
        Recomputes the rank and saves the results on the file to be read
        """

        entries: dict = self.configuration.commands
        result = []
        used_entries = []

        if self.configuration.supported_features.is_enabled("redis"):
            from search_run.events.latest_used_entries import LatestUsedEntries

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

        return self.print_entries(result)

    def print_entries(self, data: List[Tuple[str, dict]]):
        position = 1
        for name, content in data:
            try:
                content["key_name"] = name
                content["rank_position"] = position
                content["generated_acronyms"] = generate_acronyms(name)
                content_str = json.dumps(content, default=tuple, ensure_ascii=True)
            except BaseException as e:
                logging.warning(e)
                content = content
                content_str = str(content)

            position = position + 1

            content_str = f"{name.lower()}: " + content_str
            content_str = content_str.replace("\\", "\\\\")
            print(content_str)
