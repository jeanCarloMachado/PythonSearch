from typing import List

import pandas as pd

from python_search.configuration.loader import ConfigurationLoader
from python_search.llm_next_item_predictor.t5.config import T5Model
from python_search.semantic_search.distilbert import to_embedding2, to_embedding

class T5Embeddings:
    """
    Build entry embeddings and save them
    """

    pickled_location = "~/.python_search/t5_embeddings.pkl"

    def __init__(self):
        self._configuration = ConfigurationLoader().load_config()
        self.model, self.tokenizer = T5Model().load_trained_model()


    def get_embeddings(self, sentences: List[str]):
        import torch

        # Tokenize all sentences and convert to tensor format
        inputs = self.tokenizer(sentences, padding=True, truncation=True, return_tensors='pt')

        with torch.no_grad():
            # Generate the outputs from the model
            outputs = self.model.encoder(inputs['input_ids']).last_hidden_state

        # Average the embeddings to get sentence-level embeddings
        sentence_embeddings = torch.mean(outputs, dim=1)

        return sentence_embeddings


    def save_missing_keys(self):
        """
        """
        entries = self._configuration.commands
        missing_keys = list(set(self._get_missing_keys()))
        unique_keys = missing_keys
        unique_bodies = []

        for key in unique_keys:
                unique_bodies.append(key)

        embeddings = self.get_embeddings(unique_bodies)

        df_missing = pd.DataFrame()
        df_missing["key"] = unique_keys
        df_missing['body'] = unique_bodies
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


        embeddings = [self.get_embeddings([body]) for body in unique_bodies]

        df = pd.DataFrame()
        df["key"] = unique_keys
        df['body'] = unique_bodies
        df["embedding"] = embeddings

        print("Pickled embeddings to: " + self.pickled_location)
        df.to_pickle(self.pickled_location)

    def _read_dataframe(self):
        return pd.read_pickle(self.pickled_location)

    def _get_missing_keys(self) -> List[str]:
        entries = self._configuration.commands
        keys = list(entries.keys())

        df = self._read_dataframe()
        data_frame_keys = df['key'].tolist()
        missing_values = [x for x in keys if x not in data_frame_keys]
        return missing_values


def main():
    import fire
    fire.Fire(T5Embeddings)

if __name__ == "__main__":
    main()
