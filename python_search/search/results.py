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

    def __init__(self):
        self._today = datetime.datetime.now()

    @timeit
    def build_entries_result(
        self, entries: RankedEntries.type, ranking_uuid: str
    ) -> str:
        """Print results"""
        position = 1
        result = ""
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
                if "created_at" in content:
                    date_created = parser.parse(content["created_at"])
                    days_ago = (self._today - date_created).days

                    content["tags"].append(f"created_{days_ago}_days_ago")

                    if days_ago == 0:
                        content["tags"].append(f"today_created")
                    elif days_ago == 1:
                        content["tags"].append(f"yesterday_created")
                    if days_ago < 7:
                        content["tags"].append(f"this_week_created")
                    if days_ago > 7 and days_ago < 14:
                        content["tags"].append(f"previous_week_created")
                    if days_ago < 30:
                        content["tags"].append(f"this_month_created")
                    if days_ago > 30 and days_ago < 60:
                        content["tags"].append(f"previous_month_created")
                    if days_ago < 365:
                        content["tags"].append(f"this_year_created")
                    if days_ago > 365:
                        content["tags"].append(f"previous_year_created")

                content_str = json.dumps(content, default=tuple, ensure_ascii=True)
            except BaseException as e:
                logging.info(e)
                content_str = str(content)

            position = position + 1

            content_str = f"{name}:" + content_str
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
