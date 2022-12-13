from __future__ import annotations

from typing import Optional

from pydantic import BaseModel


class RunPerformed(BaseModel):
    """
    Main event of the application.
    Identifies a search being executed
    """

    # name of the entry matched
    key: str
    # for when a query was typed by the user
    # @todo rename to something more meaningful
    query_input: str
    # for when it is started from a shortcut
    shortcut: str
    # unix timestamp
    timestamp: Optional[str] = None
    rank_uuid: Optional[str] = None
    rank_position: Optional[int] = None

    @staticmethod
    def get_schema():
        return "key string, query_input string, shortcut string, rank_uuid string"
