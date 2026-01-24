from typing import List
import os
from rank_bm25 import BM25Plus as BM25
import nltk


class Bm25Search:
    DATABASE_LOCATION = "/tmp/bm25.pickle"

    NUMBER_ENTRIES_TO_RETURN = 15

    def __init__(self, entries, number_entries_to_return=None):
        self.tokenizer = nltk.tokenize.RegexpTokenizer(r"\w+")
        self.lemmatizer = nltk.stem.PorterStemmer()
        self.commands = entries
        self.entries: List[str] = list(self.commands.keys())
        self.bm25 = self.setup_bm25()
        self.number_entries_to_return = (
            number_entries_to_return if number_entries_to_return else self.NUMBER_ENTRIES_TO_RETURN
        )

    def serialize_database(self, bm25):
        import pickle

        # Store both the bm25 index and the number of entries it was built with
        cache_data = {
            "bm25": bm25,
            "corpus_size": len(self.entries),
            "entry_keys": self.entries,  # Store actual keys for validation
        }
        with open(self.DATABASE_LOCATION, "wb") as f:
            pickle.dump(cache_data, f)

    def deserialize_database(self):
        import pickle

        try:
            with open(self.DATABASE_LOCATION, "rb") as f:
                cache_data = pickle.load(f)

            # Handle old format (just bm25 object) - force rebuild
            if not isinstance(cache_data, dict) or "bm25" not in cache_data:
                self._delete_cache()
                return None

            # Verify corpus size matches current entries
            cached_size = cache_data.get("corpus_size", 0)
            current_size = len(self.entries)

            if cached_size != current_size:
                self._delete_cache()
                return None

            # If we have stored keys, verify they match exactly
            cached_keys = cache_data.get("entry_keys")
            if cached_keys is not None and cached_keys != self.entries:
                self._delete_cache()
                return None

            return cache_data["bm25"]
        except Exception:
            self._delete_cache()
            return None

    def _delete_cache(self):
        """Delete the cache file if it exists"""
        try:
            if os.path.exists(self.DATABASE_LOCATION):
                os.remove(self.DATABASE_LOCATION)
        except Exception:
            pass

    def setup_bm25(self, force_rebuild=False):
        if force_rebuild:
            return self.build_bm25()

        # Always try to load and validate cache
        if os.path.exists(self.DATABASE_LOCATION):
            bm25 = self.deserialize_database()
            if bm25 is not None:
                return bm25

        return self.build_bm25()

    def build_bm25(self):
        tokenized_corpus = [
            self.tokenize((key + str(value))) + self.split_key(key) for key, value in self.commands.items()
        ]

        bm25 = BM25(tokenized_corpus)
        self.serialize_database(bm25)

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
            matches = self.bm25.get_top_n(tokenized_query, self.entries, n=self.number_entries_to_return)
        except Exception:
            # Rebuild the index and update self.bm25
            self.bm25 = self.build_bm25()
            matches = self.bm25.get_top_n(tokenized_query, self.entries, n=self.number_entries_to_return)

        return matches

    def tokenize(self, string) -> List[str]:
        tokens = self.tokenizer.tokenize(string)
        lemmas = [self.lemmatizer.stem(t) for t in tokens]
        return lemmas


if __name__ == "__main__":
    import fire

    fire.Fire()
