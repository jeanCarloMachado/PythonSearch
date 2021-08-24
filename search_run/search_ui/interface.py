from typing import Optional, NamedTuple


class SearchResult(NamedTuple):
    result: str
    query: Optional[str]

class SearchInterface:
    def run(self, cmd: str) -> Optional[SearchResult]:
        raise Exception("Implement me")