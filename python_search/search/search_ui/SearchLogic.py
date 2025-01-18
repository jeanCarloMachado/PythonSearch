from python_search.search.search_ui.bm25_search import Bm25Search
from python_search.search.search_ui.semantic_search import SemanticSearch


from typing import Generator


class SearchLogic:
    ENABLE_SEMANTIC_SEARCH = True
    NUMBER_ENTRIES_TO_RETURN = 10

    def __init__(self, commands: dict[str, str]) -> None:
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

        if query == self.last_query and query != "" and self.last_query is not None:
            yield from self.in_results_list
            return
        self.last_query = query
        self.in_results_list = []

        bm25_results = self.search_bm25.search(query)
        bm25_results = iter(bm25_results)

        semantic_results = []
        if self.ENABLE_SEMANTIC_SEARCH:
            semantic_results = self.search_semantic.search(query)

        semantic_results = iter(semantic_results)

        self.results = []

        while True:
            if len(self.in_results_list) >= self.NUMBER_ENTRIES_TO_RETURN:
                return
            try:
                yield next(
                    self.get_a_unique_result(self.string_match(query), " string match")
                )
            except Exception:
                pass
            if len(self.in_results_list) >= self.NUMBER_ENTRIES_TO_RETURN:
                return
            try: 
                yield next(self.get_a_unique_result(bm25_results, " bm25 "))
            except Exception:
                pass
            if len(self.in_results_list) >= self.NUMBER_ENTRIES_TO_RETURN:
                return
            try:
                yield next(self.get_a_unique_result(semantic_results, " semantic "))
            except Exception:
                pass
            if len(self.in_results_list) >= self.NUMBER_ENTRIES_TO_RETURN:
                return

    def get_a_unique_result(self, given_iterator=None, key_prefix=None):
        while candidate := next(given_iterator):
            if (
                candidate not in self.in_results_list
                and candidate in self.commands.keys()
            ):
                self.in_results_list.append(candidate)
                if key_prefix and False:
                    candidate = key_prefix + candidate
                yield candidate

    def string_match(self, query: str) -> str:
        if len(query) < 3:
            return

        for i in self.commands.keys():
            if query in i:
                yield i
