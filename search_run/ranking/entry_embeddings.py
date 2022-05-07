# !/usr/bin/env python

from search_run.ranking.baseline.train import create_embeddings
from search_run.ranking.entries_loader import EntriesLoader


class EntryEmbeddings:
    def create_for_current_entries(self):
        """
        Generate embeddings for all currently existing entries
        """
        keys = EntriesLoader.load_all_keys()
        embeddings = create_indexed_embeddings(keys)

        return embeddings

    def sync(self):
        pass


def create_indexed_embeddings(keys):
    unique_keys = list(set(keys))
    embeddings = create_embeddings(unique_keys)
    embeddings_keys = dict(zip(unique_keys, embeddings))
    return embeddings_keys


if __name__ == "__main__":
    import fire

    fire.Fire(EntryEmbeddings)
