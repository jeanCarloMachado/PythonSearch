from __future__ import annotations

import datetime
import json
import logging

from python_search.search.ranked_entries import RankedEntries


class FzfOptimizedSearchResultsBuilder:
    """
    Builds the list of results ready to be consumed by fzf
    """

    degraded_message = ""

    def __init__(self):
        self._today = datetime.datetime.now()

    def build_entries_result(
        self, *, entries: RankedEntries.type, ranking_uuid: str
    ) -> str:
        """Build the string to be printed in fzf"""
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
                content["uuid"] = ranking_uuid
                content["tags"] = content["tags"] if "tags" in content else []

                initials = ""
                for word in name.split(" "):
                    if len(word):
                        initials += word[0]
                content["tags"].append(initials)

                content_str = json.dumps(content, default=tuple, ensure_ascii=True)
            except BaseException as e:
                logging.debug(e)
                content_str = str(content)

            position = position + 1

            content_str = (
                f"{name}                                                                                                            :"
                + content_str
            )
            #  replaces all single quotes for double ones
            #  otherwise the json does not get rendered
            content_str = content_str.replace("'", '"')
            print(content_str, flush=True)


def sanitize(content):
    result = ""
    for char in content:
        if char.isalnum():
            result += char
        else:
            result += " "

    return result
