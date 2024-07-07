from python_search.search.search_ui.bm25_search import Bm25Search
from python_search.search.search_ui.semantic_search import SemanticSearch


from typing import Generator


class SearchLogic:
    ENABLE_SEMANTIC_SEARCH = True
    NUMBER_ENTRIES_TO_RETURN = 6

    def __init__(self, commands) -> None:
        self.commands = commands
        self.search_bm25 = Bm25Search(
            self.commands, number_entries_to_return=self.NUMBER_ENTRIES_TO_RETURN
        )
        if self.ENABLE_SEMANTIC_SEARCH:
            self.search_semantic = SemanticSearch(
                self.commands, number_entries_to_return=self.NUMBER_ENTRIES_TO_RETURN
            )

    def search(self, query: str) -> Generator[str, None, None]:
        """
        gets 1 from each type of search at a time and merge them to remove duplicates
        """

        already_returned = []
        bm25_results = self.search_bm25.search(query)

        semantic_results = []
        if self.ENABLE_SEMANTIC_SEARCH:
            semantic_results = self.search_semantic.search(query)

        for i in range(self.NUMBER_ENTRIES_TO_RETURN):
            if (
                bm25_results[i] not in already_returned
                and bm25_results[i] in self.commands
            ):
                already_returned.append(bm25_results[i])
                yield bm25_results[i]

            if semantic_results and (
                semantic_results[i] not in already_returned
                and semantic_results[i] in self.commands
            ):
                already_returned.append(semantic_results[i])
                yield semantic_results[i]

            if len(already_returned) >= self.NUMBER_ENTRIES_TO_RETURN:
                return
