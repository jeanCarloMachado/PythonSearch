class LLMCli:
    def __init__(self):
        from python_search.ps_llm.llm_dataset import LLMDataset
        from python_search.ps_llm.t5.t5_embeddings import T5Embeddings
        from python_search.ps_llm.t5.t5_ranker import NextItemReranker
        from python_search.ps_llm.evaluation import Evaluate

        from python_search.ps_llm.t5.t5_trainer import T5Train

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
