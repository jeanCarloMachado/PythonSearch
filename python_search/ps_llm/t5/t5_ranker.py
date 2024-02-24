from typing import List, Optional

from python_search.ps_llm.t5.next_item_prompt import PromptBuilder
from python_search.ps_llm.t5.t5_model import T5Model
from python_search.ps_llm.t5.t5_embeddings import T5Embeddings
from python_search.search.entries_loader import EntriesLoader
from python_search.search.rank_utils import prepend_order_in_entries
from python_search.logger import next_item_predictor_logger


class NextItemReranker:
    """
    Rerank entries based on the predicted next item
    """

    def __init__(self):
        self.MAX_NEW_TOKENS = 30
        self.embeddings = T5Embeddings()
        self.model = T5Model.load_trained_model()
        self.logger = next_item_predictor_logger()

    def rank_entries(
        self,
        *,
        keys: Optional[List[str]] = None,
        recent_history=None,
        predicted_action: str = None,
        limit: int = None,
        prepend_order=False
    ):
        if not predicted_action:
            predicted_action = self.get_next_predicted_actions(
                recent_history=recent_history
            )

        keys: List[str] = keys
        if not keys:
            keys = EntriesLoader().load_only_keys()

        if limit:
            keys = keys[:limit]

        result = self.embeddings.rank_entries_by_query_similarity(predicted_action)
        result = [x[0] for x in result]

        if prepend_order:
            return prepend_order_in_entries(result)

        return result

    def get_prompt(self, recent_history):
        if not recent_history:
            recent_history = ["gmail", "gmail", "gmail"]
        return PromptBuilder().build_prompt_inference(history=recent_history)

    def get_next_predicted_actions(
        self, *, recent_history=None, recent_history_str=None
    ):
        if recent_history_str:
            recent_history = list(recent_history_str)
        prompt = self.get_prompt(recent_history)

        self.logger.debug(prompt)
        result = self.model.predict(prompt)
        self.logger.debug("NextItem: " + result)
        return result


def main():
    import fire

    fire.Fire(NextItemReranker)


if __name__ == "__main__":
    main()
