#!/usr/bin/env python3

from typing import List

import pandas as pd
from sklearn.metrics.pairwise import cosine_similarity

from python_search.configuration.loader import ConfigurationLoader
from python_search.semantic_search.distilbert import to_embedding2, to_embedding


class SemanticSearch:
    """
    Build entry embeddings and save them
    """

    pickled_location = "~/.python_search/bert_entry_embeddings.pkl"

    def __init__(self):
        self._configuration = ConfigurationLoader().load_config()

    def save_missing_keys(self):
        """ """
        entries = self._configuration.commands
        missing_keys = list(set(self._get_missing_keys()))
        unique_keys = missing_keys
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

        df_missing = pd.DataFrame()
        df_missing["key"] = unique_keys
        df_missing["body"] = unique_bodies
        df_missing["embedding"] = embeddings_np

        df = self._read_dataframe()
        df_result = pd.concat([df, df_missing])
        df_result.to_pickle(self.pickled_location)

    def save_all_keys(self):
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
        df["body"] = unique_bodies
        df["embedding"] = embeddings_np

        print("Pickled embeddings to: " + self.pickled_location)
        df.to_pickle(self.pickled_location)

    def _read_dataframe(self):
        return pd.read_pickle(self.pickled_location)

    def rank_entries_by_query_similarity(self, query) -> List[str]:
        from python_search.apps.notification_ui import send_notification

        send_notification(f"Starting semantic search")
        embedding_query = to_embedding([query])[0].numpy()

        df = self._read_dataframe()
        result = []
        for i, key in enumerate(df["key"].tolist()):
            similarity = cosine_similarity(
                embedding_query.reshape(1, -1), df.iloc[i]["embedding"].reshape(1, -1)
            )
            result.append((key, float(similarity)))

        result = sorted(result, key=lambda x: x[1], reverse=True)

        return [x[0] for x in result]

    def _get_missing_keys(self) -> List[str]:
        entries = self._configuration.commands
        keys = list(entries.keys())

        df = self._read_dataframe()
        data_frame_keys = df["key"].tolist()
        missing_values = [x for x in keys if x not in data_frame_keys]
        return missing_values


def main():
    import fire

    fire.Fire(SemanticSearch)


if __name__ == "__main__":
    main()
