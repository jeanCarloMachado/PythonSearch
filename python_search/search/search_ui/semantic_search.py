from python_search.search.entries_loader import EntriesLoader
import tqdm
import os

CHROMA_DB_PATH = os.environ["HOME"] + "/.chroma_python_search.db"

class SemanticSearch:
    def __init__(self, entries: dict = None, number_entries_to_return=None):
        self.get_chroma_instance()
        if entries:
            self.entries = EntriesLoader.convert_to_list_of_entries(entries)
        else:
            self.entries = EntriesLoader.load_all_entries()
        
        try:
            self.collection = self.client.get_collection("entries")
        except Exception:
            self.setup_entries()

        self.number_entries_to_return = (
            number_entries_to_return if number_entries_to_return else 15
        )

    def get_chroma_instance(self):
        import chromadb
        self.client = chromadb.PersistentClient(path=CHROMA_DB_PATH)
        return self.client

    def setup_entries(self):
        print("Setting up documents")
        existing_ids = self.client.get_or_create_collection("entries").get()["ids"]
        missing_entries = [
            entry for entry in self.entries if entry.key not in existing_ids
        ]
        print("Found ", len(missing_entries), " missing entries")

        collection = self.client.get_or_create_collection("entries")
        for entry in tqdm.tqdm(missing_entries):
            collection.upsert(
                documents=[
                    entry.key + " " + entry.get_content_str() + entry.get_type_str()
                ],
                ids=[entry.key],
            )

        return collection

    def search(self, query: str):
        if not query:
            query = ""
        results = self.collection.query(
            query_texts=[query], n_results=self.number_entries_to_return, include=[]
        )["ids"][0]
        return results


if __name__ == "__main__":
    import fire

    fire.Fire()
