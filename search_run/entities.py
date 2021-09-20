from typing import NamedTuple, Optional


class SearchResult(NamedTuple):
    result: str
    query: Optional[str]
