import os
from typing import List, Optional

import tqdm

from python_search.search.entries_loader import EntriesLoader

CHROMA_DB_PATH = os.path.join(os.environ["HOME"], ".chroma_python_search.db")


class SemanticSearch:
    """Semantic search using ChromaDB for embedding-based similarity search."""

    DEFAULT_RESULTS = 15

    def __init__(self, entries: Optional[dict] = None, number_entries_to_return: Optional[int] = None):
        self._init_client()
        self.entries = (
            EntriesLoader.convert_to_list_of_entries(entries) if entries else EntriesLoader.load_all_entries()
        )
        self.number_entries_to_return = number_entries_to_return or self.DEFAULT_RESULTS
        self._init_collection()

    def _init_client(self) -> None:
        import chromadb

        self.client = chromadb.PersistentClient(path=CHROMA_DB_PATH)

    def _init_collection(self) -> None:
        try:
            self.collection = self.client.get_collection("entries")
        except ValueError:
            self._setup_entries()

    def _setup_entries(self) -> None:
        print("Setting up documents")
        collection = self.client.get_or_create_collection("entries")
        existing_ids = set(collection.get()["ids"])
        missing_entries = [entry for entry in self.entries if entry.key not in existing_ids]
        print(f"Found {len(missing_entries)} missing entries")

        for entry in tqdm.tqdm(missing_entries):
            collection.upsert(
                documents=[f"{entry.key} {entry.get_content_str()}{entry.get_type_str()}"],
                ids=[entry.key],
            )

        self.collection = collection

    def search(self, query: str) -> List[str]:
        query = query or ""
        results = self.collection.query(query_texts=[query], n_results=self.number_entries_to_return, include=[])[
            "ids"
        ][0]
        return results
