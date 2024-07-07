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
        self.last_query = None
        self.in_results_list = []

    def search(self, query: str) -> Generator[str, None, None]:
        """
        gets 1 from each type of search at a time and merge them to remove duplicates
        """

        if query == self.last_query:
            yield from self.in_results_list
            return


        self.last_query = query
        self.in_results_list = []
        bm25_results = self.search_bm25.search(query)

        semantic_results = []
        if self.ENABLE_SEMANTIC_SEARCH:
            semantic_results = self.search_semantic.search(query)
        

        self.results = []

        for i in range(self.NUMBER_ENTRIES_TO_RETURN):
            if len(self.in_results_list) == self.NUMBER_ENTRIES_TO_RETURN:
                return

            if (
                bm25_results[i] not in self.in_results_list
                and bm25_results[i] in self.commands
            ):
                self.in_results_list.append(bm25_results[i])
                yield bm25_results[i]

            if semantic_results and (
                semantic_results[i] not in self.in_results_list
                and semantic_results[i] in self.commands
            ):
                self.in_results_list.append(semantic_results[i])
                yield semantic_results[i]

        
        
