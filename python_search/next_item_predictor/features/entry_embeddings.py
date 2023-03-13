from typing import List, Optional

import numpy as np

import os
from python_search.configuration.loader import ConfigurationLoader
from python_search.next_item_predictor.features.inference_embeddings.inference_embeddings import \
    create_embeddings_from_strings



class EntryEmbeddings:

    _embeddings = None
    pickled_location = "/tmp/entry_embeddings.pkl"

    def __init__(self, df):
        self._df = df

    @staticmethod
    def build():
        """
        Create an embedding dict
        """
        configuration = ConfigurationLoader().load_config()
        entries = configuration.commands

        keys = list(entries.keys())
        unique_keys = list(set(keys))
        unique_bodies = []

        for key in unique_keys:
            if key in entries:
                body = str(entries[key])
                print(f"For key '{key}', found body to encode: {body}")
                unique_bodies.append(key + " " + body)
            else:
                print(f"Could not find body for key: {key}")
                unique_bodies.append(key)

        only_embeddings = create_embeddings_from_strings(unique_bodies)
        return EntryEmbeddings(EntryEmbeddings.to_pd(unique_keys, only_embeddings))


    @staticmethod
    def to_pd(keys, embeddings):
        import pandas as pd
        df = pd.DataFrame(zip(keys, embeddings), columns=["key", "embedding"])
        df.set_index("key", inplace=True)

        return df

    def serialize(self):
        self._df.to_pickle("/tmp/entry_embeddings.pkl")

    @staticmethod
    def load_cached_or_build():
        import pandas as pd
        if os.path.exists(EntryEmbeddings.pickled_location):
            return EntryEmbeddings(pd.read_pickle(EntryEmbeddings.pickled_location))

        return EntryEmbeddings.build()

    def get_key_embedding(self, key) -> Optional[np.ndarray]:
        match = self._df[self._df.index == key].values

        if len(match):
            return match[0][0]

        return None


    def all_keys(self) -> List[str]:
        return self._df.index.values


def main():
    import fire
    fire.Fire(EntryEmbeddings)

if __name__ == "__main__":
    main()

