
from python_search.ps_llm.llm_dataset import LLMDataset
from python_search.ps_llm.t5.t5_model import T5Model
from tqdm import tqdm

class Evaluate():

    def from_pretrained(self, model_path=None):
        """
        Performs the evaluation of a model given its path and the latest dataset
        """
        data = LLMDataset().load_validation()
        model = T5Model.load_trained_model(model_path)
        return self.perform(model, data)

    def perform(self, model, data):
        similarity = Similarity()
        print("Starting to predict all rows")
        data["predicted"] = [model.predict(row["prompt"]) for index, row in tqdm(data.iterrows())]
        print("Compute similarity between predicted and label")
        data["similarity"] = [
            similarity.compute(row["predicted"], row["label"])
            for index, row in tqdm(data.iterrows())
        ]

        similarity_mean = data["similarity"].mean()

        print("Sample of rows")
        print(data.iloc[[0]])
        print(data.iloc[[1]])
        print(data.iloc[[-1]])

        return similarity_mean


class Similarity:
    def __init__(self):
        from sentence_transformers import SentenceTransformer
        self.model = SentenceTransformer("distilbert-base-nli-mean-tokens")

    def compute(self, sentence1, sentence2):
        from sentence_transformers import util
        sentence_embeddings = self.model.encode([sentence1, sentence2])
        result = util.pytorch_cos_sim(sentence_embeddings[0], sentence_embeddings[1])
        return float(result[0][0])


if __name__ == "__main__":
    import fire
    fire.Fire()
