from typing import Optional

from search_run.entities import SearchResult


class SearchInterface:
    def run(self, cmd: str) -> Optional[SearchResult]:
        raise Exception("Implement me")
