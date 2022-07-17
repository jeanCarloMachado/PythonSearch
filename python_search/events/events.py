""" Centralize all events definitions to help in the data discovery """
from dataclasses import dataclass

from pydantic import BaseModel


@dataclass
class SearchRunPerformed:
    """
    Main event of the application.
    Identifies a search being executed
    """

    # name of the entry matched
    key: str
    # for when a query was typed by the user
    query_input: str
    # for when it is started from a shortcut
    shortcut: str

    @staticmethod
    def get_schema():
        return "key string, query_input string, shortcut string"


class RegisterExecuted(BaseModel):
    key: str
    content: str
