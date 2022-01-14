from __future__ import annotations

import datetime
import json
from collections import namedtuple
from typing import List, Tuple

import pandas as pd
import pyspark.sql.functions as F
from dateutil.relativedelta import relativedelta
from grimoire.file import write_file

from search_run.base_configuration import BaseConfiguration
from search_run.config import DataPaths
from search_run.core_entities import RankingAlgorithms
from search_run.observability.logger import configure_logger

logger = configure_logger()


class RankingGenerator:
    """
    Write to the file all the commands and generates shortcuts
    """

    ModelInfo = namedtuple("ModelInfo", "features label")
    model_info = ModelInfo(["position", "key_lenght"], "input_lenght")

    def __init__(self, configuration: BaseConfiguration):
        self.configuration = configuration
        self.cached_file = configuration.cached_filename

    def recompute_rank(self):
        """
        Recomputes the rank and saves the results on the file to be read
        """

        entries: dict = self.load_entries()
        result = []

        for key in entries.keys():
            result.append((key, entries[key]))

        return self._export_to_file(result)

    def load_entries(self):
        """ Loads the current state of the art of search run entries"""
        return self.configuration.commands

    def _export_to_file(self, data: List[Tuple[str, dict]]):
        fzf_lines = ""
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
            fzf_lines += f"{name.lower()}: " + content_str + "\n"

        fzf_lines = fzf_lines.replace("\\", "\\\\")
        write_file(self.configuration.cached_filename, fzf_lines)
