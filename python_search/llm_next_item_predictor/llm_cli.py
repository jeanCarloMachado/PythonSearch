from python_search.llm_next_item_predictor.next_item_llm_dataset import LLMDataset
from python_search.llm_next_item_predictor.t5.trainer import T5Train


class LLMCli:
    def __init__(self):
        self.t5_trainer = T5Train()
        self.dataset = LLMDataset()


def main():
    import fire
    fire.Fire(LLMCli)

if __name__ == "__main__":
    main()

