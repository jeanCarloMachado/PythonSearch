from dataclasses import dataclass

from pydantic import BaseModel

""" Centralize all events definitions to help in the data discovery """


@dataclass
class SearchPerformed:
    # the query typed by the user
    given_input: str
    # name of the entry matched
    key: str


class RegisterExecuted(BaseModel):
    key: str
    content: str
