from typing import List

from python_search.core_entities.core_entities import Entry
from python_search.search.entries_loader import EntriesLoader
import tqdm
import os


class SemanticSearch:

    def __init__(self, number_entries_to_return=None):
        self.setup()
        self.number_entries_to_return = (
            number_entries_to_return if number_entries_to_return else 15
        )

    def setup(self):
        import chromadb

        self.chroma_path = os.environ["HOME"] + "/.chroma_python_search.db"
        self.client = chromadb.PersistentClient(path=self.chroma_path)

        try:
            self.collection = self.client.get_collection("entries")
        except:
            print("Collection not found")
            self.collection = self.setup_entries()

    def setup_entries(self):
        collection = self.client.get_or_create_collection("entries")

        loader = EntriesLoader()
        # load entries
        entries: List[Entry] = loader.load_all_entries()

        for entry in tqdm.tqdm(entries, total=loader.entries_total()):
            collection.upsert(
                documents=[
                    entry.key + " " + entry.get_content_str() + entry.get_type_str()
                ],
                ids=[entry.key],
            )

        return collection

    def search(self, query: str):
        results = self.collection.query(
            query_texts=[query], n_results=self.number_entries_to_return
        )["ids"][0]
        return results


if __name__ == "__main__":
    import fire

    fire.Fire(SemanticSearch)
