from typing import List


class Search:

    NUMBER_ENTRIES_TO_RETURN= 15
    def __init__(self):
        import nltk
        self.tokenizer = nltk.tokenize.RegexpTokenizer(r"\w+")
        self.lemmatizer = nltk.stem.WordNetLemmatizer()
        from python_search.configuration.loader import ConfigurationLoader
        self.commands = ConfigurationLoader().load_config().commands
        self.entries: List[str] = list(self.commands.keys())
        self.bm25 = self.setup_bm25()

    def setup_bm25(self):
        tokenized_corpus = [
            self.tokenize((key + str(value))) for key, value in self.commands.items()
        ]
        from rank_bm25 import BM25Okapi as BM25

        bm25 = BM25(tokenized_corpus)
        return bm25

    def search(self, query):
        if not query:
            return self.entries[0: self.NUMBER_ENTRIES_TO_RETURN], []


        tokenized_query = self.tokenize(query)

        matches = self.bm25.get_top_n(
            tokenized_query, self.entries, n=self.NUMBER_ENTRIES_TO_RETURN
        )

        return matches, tokenized_query


    def tokenize(self, string):
        tokens = self.tokenizer.tokenize(string)
        lemmas = [self.lemmatizer.lemmatize(t) for t in tokens]
        return lemmas
