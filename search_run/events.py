from dataclasses import dataclass


@dataclass
class SearchPerformed:
    # the query typed by the user
    given_input: str
    # name of the entry matched
    key: str
