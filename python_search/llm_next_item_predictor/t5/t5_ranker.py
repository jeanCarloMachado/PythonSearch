from typing import List, Optional

import torch

from python_search.llm_next_item_predictor.next_item_llm_dataset import LLMDataset
from python_search.llm_next_item_predictor.t5.config import T5Model
from python_search.llm_next_item_predictor.t5.t5_embeddings import T5Embeddings
from python_search.search.entries_loader import EntriesLoader
from python_search.search.rank_utils import prepend_order_in_entries
from python_search.logger import setup_generic_stdout_logger


class NextItemReranker:
    """
    Rerank entries based on the predicted next item
    """

    def __init__(self):
        self.model, self.tokenizer = T5Model().load_trained_model()
        self.MAX_NEW_TOKENS = 30
        self.embeddings = T5Embeddings()
        self.logger = setup_generic_stdout_logger(NextItemReranker.__name__)

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
            keys = EntriesLoader().load_all_keys()

        if limit:
            keys = keys[:limit]

        result = self.embeddings.rank_entries_by_query_similarity(predicted_action)
        result = [x[0] for x in result]

        if prepend_order:
            return prepend_order_in_entries(result)


        return result

    def get_prompt(self, recent_history):
        LIMIT = 3
        if not recent_history:
            recent_history = ["gmail", "gmail", "gmail"]
        recent_history = recent_history[:LIMIT]

        return LLMDataset.PROMPT_START + ",".join(recent_history)

    def get_next_predicted_actions(
        self, *, recent_history=None, recent_history_str=None
    ):
        if recent_history_str:
            recent_history = list(recent_history_str)

        # Load the model
        # Now you can use the model for prediction
        with torch.no_grad():
            inputs = self.get_prompt(recent_history)

            inputs_tokenized = self.tokenizer.encode_plus(inputs, return_tensors="pt")
            input_ids = inputs_tokenized["input_ids"].to("cpu")
            attention_mask = inputs_tokenized["attention_mask"].to("cpu")

            # Generate prediction
            outputs = self.model.generate(
                input_ids=input_ids,
                attention_mask=attention_mask,
                max_new_tokens=self.MAX_NEW_TOKENS,
            )

            # Decode the prediction
            predicted_text = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
        self.logger.debug("NextItem: " + predicted_text + " From input:" +inputs)
        return predicted_text


def main():
    import fire

    fire.Fire()


if __name__ == "__main__":
    main()
