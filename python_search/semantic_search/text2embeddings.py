#!/usr/bin/env python3

import time
from functools import wraps
from typing import Optional, List

import numpy as np
import pandas as pd
from sklearn.metrics.pairwise import cosine_similarity

from python_search.configuration.loader import ConfigurationLoader
from python_search.semantic_search.distilbert import to_embedding2, to_embedding


class BertEntryEmbeddings:
    """
    Build entry embeddings and save them
    """

    pickled_location = "/tmp/bert_entry_embeddings.pkl"

    def __init__(self):
        self._configuration = ConfigurationLoader().load_config()

    def save_all(self):
        """
        Create an embedding dict
        """
        entries = self._configuration.commands

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


        embeddings = to_embedding2(unique_bodies)
        embeddings_np = [embedding.numpy() for embedding in embeddings]

        df = pd.DataFrame()
        df["key"] = unique_keys
        df['body'] = unique_bodies
        df["embedding"] = embeddings_np

        print("Pickled embeddings to: " + self.pickled_location)
        df.to_pickle(self.pickled_location)


    def rank_entries_by_query_similarity(self, query)->List[str]:

        embedding_query = to_embedding([query])[0].numpy()

        df = pd.read_pickle(self.pickled_location)
        result = []
        for i, key in enumerate(df['key'].tolist()):
            similarity = cosine_similarity(embedding_query.reshape(1, -1), df.iloc[i]['embedding'].reshape(1, -1))
            result.append((key, float(similarity)))

        result = sorted(result, key=lambda x: x[1], reverse=True)

        return [x[0] for x in result]


if __name__ == "__main__":
    import fire

    fire.Fire()
