from typing import List

import os
import pandas as pd
from tqdm import tqdm

from python_search.configuration.loader import ConfigurationLoader
from python_search.ps_llm.t5.t5_model import T5Model


class T5Embeddings:
    """
    Build entry embeddings and save them
    """

    HOME = os.environ["HOME"]
    pickled_location = HOME + "/.python_search/t5_embeddings.pkl"

    def __init__(self):
        self._configuration = ConfigurationLoader().load_config()
        llm_model = T5Model.load_trained_model()
        self.model, self.tokenizer = llm_model.model, llm_model.tokenizer

    def compute_embeddings(self, sentences: List[str]):
        import torch

        # Tokenize all sentences and convert to tensor format
        inputs = self.tokenizer(
            sentences, padding=True, truncation=True, return_tensors="pt"
        )

        with torch.no_grad():
            # Generate the outputs from the model
            outputs = self.model.encoder(inputs["input_ids"]).last_hidden_state

        # Average the embeddings to get sentence-level embeddings
        sentence_embeddings = torch.mean(outputs, dim=1)

        return sentence_embeddings

    def save_all_keys(self):
        """
        Create all keys
        """
        print("Saving all keys as pandas dataframe")
        entries = self._configuration.commands
        keys = list(entries.keys())
        unique_keys = list(set(keys))

        unique_bodies = []
        for key in unique_keys:
            if key in entries:
                unique_bodies.append(key)

        embeddings = [self.compute_embeddings([body]) for body in tqdm(unique_bodies)]

        df = pd.DataFrame()
        df["key"] = unique_keys
        df["body"] = unique_bodies
        df["embedding"] = embeddings

        print("Pickled embeddings to: " + self.pickled_location)
        df.to_pickle(self.pickled_location)

    def save_missing_keys(self):
        """
        Create all missing entries in the embedding of p5
        """
        from python_search.apps.notification_ui import send_notification

        send_notification(f"Saving missing keys as pandas dataframe")

        entries = self._configuration.commands
        missing_keys = list(set(self._get_missing_keys()))
        unique_keys = missing_keys
        unique_bodies = []

        for key in unique_keys:
            unique_bodies.append(key)

        embeddings = [self.compute_embeddings([body]) for body in tqdm(unique_bodies)]

        df_missing = pd.DataFrame()
        df_missing["key"] = unique_keys
        df_missing["body"] = unique_bodies
        df_missing["embedding"] = embeddings

        df = self._read_dataframe()
        df_result = pd.concat([df, df_missing])
        df_result.to_pickle(self.pickled_location)

    def rank_entries_by_query_similarity(self, query) -> List[str]:
        import torch

        embedding_query = self.compute_embeddings([query])[0]

        df = self._read_dataframe()
        result = []
        for i, key in enumerate(df["key"].tolist()):
            similarity = torch.nn.functional.cosine_similarity(
                embedding_query, df.iloc[i]["embedding"][0], dim=0
            )
            result.append((key, float(similarity)))

        result = sorted(result, key=lambda x: x[1], reverse=True)

        return result

    def _read_dataframe(self):
        if not os.path.exists(self.pickled_location):
            raise Exception(
                "No t5 pickled embeddings found at: " + self.pickled_location
            )
        return pd.read_pickle(self.pickled_location)

    def _get_missing_keys(self) -> List[str]:
        entries = self._configuration.commands
        keys = list(entries.keys())

        df = self._read_dataframe()
        data_frame_keys = df["key"].tolist()
        missing_values = [x for x in keys if x not in data_frame_keys]
        return missing_values


def main():
    import fire

    fire.Fire(T5Embeddings)


if __name__ == "__main__":
    main()
