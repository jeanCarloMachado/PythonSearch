from typing import List

from python_search.logger import setup_term_ui_logger
from python_search.search.search_ui.bm25_search import Bm25Search

logger = setup_term_ui_logger()


class QueryLogic:
    NUMBER_ENTRIES_TO_RETURN = 50
    ENABLE_SEMANTIC_SEARCH = False
    ENABLE_BM25_SEARCH = True

    def __init__(self, commands: dict[str, str]) -> None:
        self.commands = commands
        if self.ENABLE_BM25_SEARCH:
            self.search_bm25 = Bm25Search(self.commands, number_entries_to_return=self.NUMBER_ENTRIES_TO_RETURN)
        if self.ENABLE_SEMANTIC_SEARCH:
            from python_search.search.search_ui.semantic_search import SemanticSearch

            self.search_semantic = SemanticSearch(self.commands, number_entries_to_return=self.NUMBER_ENTRIES_TO_RETURN)
        self.last_query = None
        self.in_results_list = []

    def search(self, query: str) -> List[str]:
        """
        gets results from different search methods and merge them to remove duplicates
        """

        if query == self.last_query and query != "" and self.last_query is not None:
            return self.in_results_list

        logger.info("Query: '{}'".format(query))
        self.last_query = query
        self.in_results_list = []

        try:
            # Get results from different search methods
            string_results = list(self.string_match(query))

            bm25_results = []
            if self.ENABLE_BM25_SEARCH:
                bm25_results = self.search_bm25.search(query)

            semantic_results = []
            if self.ENABLE_SEMANTIC_SEARCH:
                semantic_results = self.search_semantic.search(query)

            logger.info("Starting query logic merge")

            # Merge results with priority
            all_results = []

            if len(query) <= 3:
                # For short queries, prioritize exact string matches
                all_results.extend(string_results)
                all_results.extend(bm25_results)
            else:
                # For longer queries, prioritize BM25 then string matching
                all_results.extend(bm25_results)
                all_results.extend(string_results)

            all_results.extend(semantic_results)

            # Remove duplicates while preserving order
            seen = set()
            for result in all_results:
                if result not in seen and result in self.commands.keys():
                    self.in_results_list.append(result)
                    seen.add(result)
                    if len(self.in_results_list) >= self.NUMBER_ENTRIES_TO_RETURN:
                        break

            return self.in_results_list

        except Exception as e:
            logger.error(f"Error in search: {e}")
            return []

    def string_match(self, query: str) -> List[str]:
        """String matching that returns a list instead of generator"""
        results = []

        try:
            if not query:
                # For empty queries, return all keys but limit to avoid performance issues
                count = 0
                for key in self.commands.keys():
                    if count >= self.NUMBER_ENTRIES_TO_RETURN:
                        break
                    results.append(key)
                    count += 1
                return results

            # Convert query to lowercase for case-insensitive search
            query_lower = query.lower()
            count = 0

            # First pass: exact key matches (fastest)
            for key in self.commands.keys():
                if count >= self.NUMBER_ENTRIES_TO_RETURN:
                    break
                if query_lower in key.lower():
                    results.append(key)
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
                                results.append(key)
                                count += 1
                        except:
                            # Skip entries that can't be converted to string
                            continue

            return results

        except Exception as e:
            logger.error(f"Error in string_match: {e}")
            return results
