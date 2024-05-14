from python_search.search.entries_loader import EntriesLoader
import chromadb
import tqdm
import os

CHROMA_DB_PATH = os.environ["HOME"] + "/.chroma_python_search.db"

class SemanticSearch:
    def __init__(self, entries: dict = None, number_entries_to_return=None):
        self.get_chroma_instance()
        self.collection = self.client.get_collection("entries")
        if entries:
            self.entries = EntriesLoader.convert_to_list_of_entries(entries)
        else:
            self.entries = EntriesLoader.load_all_entries()

        self.number_entries_to_return = (
            number_entries_to_return if number_entries_to_return else 15
        )


    def get_chroma_instance(self):
        self.client = chromadb.PersistentClient(path=CHROMA_DB_PATH)
        return self.client


    def setup_entries(self):
        collection = self.client.get_or_create_collection("entries")

        for entry in tqdm.tqdm(self.entries):
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
            query_texts=[query], n_results=self.number_entries_to_return,
            include=[]
        )["ids"][0]
        return results

def chroma_run_webserver():
    cmd = 'chroma run --path ' + CHROMA_DB_PATH
    print(cmd)
    os.system(cmd)

if __name__ == "__main__":
    import fire
    fire.Fire()
