from typing import List

from python_search.core_entities.core_entities import Entry
from python_search.search.entries_loader import EntriesLoader
import tqdm
import os


class SemanticSearch:

    def setup(self):
        import chromadb
        self.chroma_path = os.environ['HOME'] + '/.chroma_python_search.db'
        self.client = chromadb.PersistentClient(path=self.chroma_path)

        try:
            self.collection = self.client.get_collection('entries')
        except:
            print('Collection not found')
            self.collection = self.setup_entries()


    def setup_entries(self):

        collection = self.client.get_or_create_collection('entries')

        # load entries
        entries: List[Entry] = EntriesLoader().load_all_entries()


        for entry in tqdm.tqdm(entries):
            collection.add(
                documents=[entry.key + ' ' + entry.content_str() + entry.get_type_str()],
                ids=[entry.key],
            )

        return collection


if __name__ == "__main__":
    import fire
    fire.Fire(SemanticSearch)
