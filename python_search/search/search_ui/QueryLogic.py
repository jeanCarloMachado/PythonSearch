from python_search.logger import setup_term_ui_logger
from python_search.search.search_ui.bm25_search import Bm25Search
from python_search.search.search_ui.semantic_search import SemanticSearch


from typing import Generator, Iterator

logger = setup_term_ui_logger()
class QueryLogic:
    NUMBER_ENTRIES_TO_RETURN = 7
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

        while True:
            if len(self.in_results_list) >= self.NUMBER_ENTRIES_TO_RETURN:
                return

            try:
                yield next(self.get_a_unique_result(self.string_match(query)))
            except StopIteration:
                logger.info("StopIteration triggered for string match with query: '" + query + "'")

            if len(self.in_results_list) >= self.NUMBER_ENTRIES_TO_RETURN:
                return

            if self.ENABLE_BM25_SEARCH:
                try:
                    yield next(self.get_a_unique_result(bm25_results))
                except StopIteration:
                    logger.info("StopIteration triggered for bm25")

            if len(self.in_results_list) >= self.NUMBER_ENTRIES_TO_RETURN:
                return

            if self.ENABLE_SEMANTIC_SEARCH:
                try:
                    yield next(self.get_a_unique_result(semantic_results))
                except StopIteration:
                    logger.info("StopIteration triggered for semantic")

            if len(self.in_results_list) >= self.NUMBER_ENTRIES_TO_RETURN:
                return

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
        for key in self.commands.keys():
            if not query:
                yield key
            elif query in key: 
                yield key
            elif query in str(self.commands[key]):
                yield key

