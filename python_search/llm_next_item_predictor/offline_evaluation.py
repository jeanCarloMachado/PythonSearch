
from python_search.llm_next_item_predictor.llm_dataset import LLMDataset

class Evaluate():

    def from_pandas(self):
        df = LLMDataset().load()
        X = df['prompt'].tolist()
        Y = df['label'].tolist()

        self.perform(X, Y)


    def perform(self, X, Y):
        similarity = Similarity()
        pass



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
