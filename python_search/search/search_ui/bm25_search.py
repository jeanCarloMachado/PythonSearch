from typing import List
import os
from rank_bm25 import BM25Plus as BM25
import nltk
from python_search.entry_change import EntryChangeDetector


class Bm25Search:
    DATABASE_LOCATION = "/tmp/bm25.pickle"

    NUMBER_ENTRIES_TO_RETURN = 15

    def __init__(self, entries, number_entries_to_return=None):
        self.tokenizer = nltk.tokenize.RegexpTokenizer(r"\w+")
        self.lemmatizer = nltk.stem.PorterStemmer()
        self.commands = entries
        self.entries: List[str] = list(self.commands.keys())
        self.entry_change_detector = EntryChangeDetector()
        self.bm25 = self.setup_bm25()
        self.number_entries_to_return = (
            number_entries_to_return
            if number_entries_to_return
            else self.NUMBER_ENTRIES_TO_RETURN
        )

    def searialize_database(self, bm25):
        import pickle

        with open(self.DATABASE_LOCATION, "wb") as f:
            pickle.dump(bm25, f)

        print("New bm25 config saved at /tmp/bm25.pickle")

    def desearialize_database(self):
        import pickle

        with open(self.DATABASE_LOCATION, "rb") as f:
            return pickle.load(f)

    def setup_bm25(self, force_rebuild=False):
        if (
            os.path.exists(self.DATABASE_LOCATION)
            and self.entry_change_detector.has_changed() is False
        ):
            return self.desearialize_database()

        return self.build_bm25()

    def build_bm25(self):
        tokenized_corpus = [
            self.tokenize((key + str(value))) + self.split_key(key)
            for key, value in self.commands.items()
        ]

        bm25 = BM25(tokenized_corpus)
        self.searialize_database(bm25)

        return bm25

    def split_key(self, key):
        """
        Create more combinations of initials for searching the document
        """
        result = []

        initials = ""
        for word in key.split(" "):
            if len(word) < 1:
                continue
            result += word[0]
            initials += word[0]

        result.append(initials)

        return result

    def search(self, query: List[str] = None) -> List[str]:
        if not query:
            return self.entries[0 : self.number_entries_to_return]

        tokenized_query = self.tokenize(query)

        try:
            matches = self.bm25.get_top_n(
                tokenized_query, self.entries, n=self.number_entries_to_return
            )
        except Exception:
            self.build_bm25()
            matches = self.bm25.get_top_n(
                tokenized_query, self.entries, n=self.number_entries_to_return
            )

        return matches

    def tokenize(self, string) -> List[str]:
        tokens = self.tokenizer.tokenize(string)
        lemmas = [self.lemmatizer.stem(t) for t in tokens]
        return lemmas


if __name__ == "__main__":
    import fire

    fire.Fire()
