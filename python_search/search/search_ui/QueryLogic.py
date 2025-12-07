from python_search.logger import setup_term_ui_logger
from python_search.search.search_ui.bm25_search import Bm25Search
from python_search.search.search_ui.semantic_search import SemanticSearch


from typing import Generator, Iterator

logger = setup_term_ui_logger()
class QueryLogic:
    NUMBER_ENTRIES_TO_RETURN = 50
    ENABLE_SEMANTIC_SEARCH = False
    ENABLE_BM25_SEARCH = True

    def __init__(self, commands: dict[str, str]) -> None:
        self.commands = commands
        if self.ENABLE_BM25_SEARCH:
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

        logger.info("Query: '{}'".format(query))
        self.last_query = query
        self.in_results_list = []

        bm25_results = []
        if self.ENABLE_BM25_SEARCH:
            bm25_results = self.search_bm25.search(query)
        bm25_results = iter(bm25_results)

        semantic_results = []
        if self.ENABLE_SEMANTIC_SEARCH:
            semantic_results = self.search_semantic.search(query)
        semantic_results = iter(semantic_results)

        self.results = []
        
        logger.info("Starting query logic loop")

        # Get iterators for all search methods
        string_match_iter = self.get_a_unique_result(self.string_match(query))
        
        # Prioritize string matching for short queries, BM25 for longer ones
        search_methods = []
        if len(query) <= 3:
            # For short queries, prioritize exact string matches
            search_methods = [string_match_iter]
            if self.ENABLE_BM25_SEARCH:
                search_methods.append(self.get_a_unique_result(bm25_results))
        else:
            # For longer queries, prioritize BM25 then string matching
            if self.ENABLE_BM25_SEARCH:
                search_methods.append(self.get_a_unique_result(bm25_results))
            search_methods.append(string_match_iter)
            
        if self.ENABLE_SEMANTIC_SEARCH:
            search_methods.append(self.get_a_unique_result(semantic_results))

        # Round-robin through search methods
        while len(self.in_results_list) < self.NUMBER_ENTRIES_TO_RETURN and search_methods:
            methods_to_remove = []
            
            for i, method in enumerate(search_methods):
                try:
                    yield next(method)
                    if len(self.in_results_list) >= self.NUMBER_ENTRIES_TO_RETURN:
                        return
                except StopIteration:
                    methods_to_remove.append(i)
            
            # Remove exhausted iterators
            for i in reversed(methods_to_remove):
                search_methods.pop(i)

    def get_a_unique_result(self, given_iterator: Iterator[str]):
        try:
            while candidate := next(given_iterator):
                if (
                    candidate not in self.in_results_list
                    and candidate in self.commands.keys()
                ):
                    self.in_results_list.append(candidate)
                    logger.info("Number of results in in_results_list" + str(len(self.in_results_list)))
                    logger.info("candidate" + candidate)
                    yield candidate
        except StopIteration:
            logger.info("StopIteration triggered for get_a_unique_result")
            return


    def string_match(self, query: str) -> Iterator[str]:
        if not query:
            # For empty queries, return all keys but limit to avoid performance issues
            count = 0
            for key in self.commands.keys():
                if count >= self.NUMBER_ENTRIES_TO_RETURN:
                    break
                yield key
                count += 1
            return
            
        # Convert query to lowercase for case-insensitive search
        query_lower = query.lower()
        count = 0
        
        # First pass: exact key matches (fastest)
        for key in self.commands.keys():
            if count >= self.NUMBER_ENTRIES_TO_RETURN:
                break
            if query_lower in key.lower():
                yield key
                count += 1
        
        # Second pass: content matches (slower, only if needed)
        if count < self.NUMBER_ENTRIES_TO_RETURN:
            for key in self.commands.keys():
                if count >= self.NUMBER_ENTRIES_TO_RETURN:
                    break
                # Skip if already matched in first pass
                if query_lower not in key.lower():
                    try:
                        command_str = str(self.commands[key]).lower()
                        if query_lower in command_str:
                            yield key
                            count += 1
                    except:
                        # Skip entries that can't be converted to string
                        continue

