""" Centralize all events definitions to help in the _entries discovery """
from dataclasses import dataclass

from pydantic import BaseModel


class SearchRunPerformed(BaseModel):
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

    @staticmethod
    def get_schema():
        return "key string, query_input string, shortcut string"
