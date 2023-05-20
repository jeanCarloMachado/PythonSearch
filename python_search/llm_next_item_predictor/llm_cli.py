from python_search.llm_next_item_predictor.llm_dataset import LLMDataset
from python_search.llm_next_item_predictor.t5.t5_embeddings import T5Embeddings
from python_search.llm_next_item_predictor.t5.t5_ranker import NextItemReranker
from python_search.llm_next_item_predictor.t5.trainer import T5Train
from python_search.llm_next_item_predictor.evaluation import Evaluate


class LLMCli:
    def __init__(self):
        self.t5_trainer = T5Train
        self.dataset = LLMDataset
        self.t5_ranker = NextItemReranker
        self.t5_embeddings = T5Embeddings
        self.evaluation = Evaluate


def main():
    import fire

    fire.Fire(LLMCli)


if __name__ == "__main__":
    main()
