from __future__ import annotations

import datetime
import json
import logging
import os

from dateutil import parser

from python_search.acronyms import generate_acronyms
from python_search.infrastructure.performance import timeit
from python_search.search.ranked_entries import RankedEntries


class FzfOptimizedSearchResults:
    """
    Builds the list of results ready to be consumed by fzf
    """

    degraded_message = ""

    def __init__(self):
        self._today = datetime.datetime.now()

    @timeit
    def build_entries_result(
        self, entries: RankedEntries.type, ranking_uuid: str
    ) -> str:
        """Print results"""
        position = 1
        result = ""
        if self.degraded_message:
            result = f"Degraded: {self.degraded_message}\n"
        for name, content in entries:
            try:
                if "snippet" in content:
                    content["snippet"] = sanitize(content["snippet"])
                if "cmd" in content:
                    content["cmd"] = sanitize(content["cmd"])

                content["key_name"] = name
                content["position"] = position
                content["generated_acronyms"] = generate_acronyms(name)
                content["uuid"] = ranking_uuid
                content["tags"] = content["tags"] if "tags" in content else []

                content_str = json.dumps(content, default=tuple, ensure_ascii=True)
            except BaseException as e:
                logging.info(e)
                content_str = str(content)

            position = position + 1

            content_str = (
                f"{name}                                                      :"
                + content_str
            )
            #  replaces all single quotes for double ones
            #  otherwise the json does not get rendered
            content_str = content_str.replace("'", '"')
            if os.getenv("ENABLE_TIME_IT"):
                # do not print if enable timeit is on
                continue
            result += content_str + "\n"
        return result


def sanitize(content):
    result = ""
    for char in content:
        if char.isalnum():
            result += char
        else:
            result += " "

    return result
