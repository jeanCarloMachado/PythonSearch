from python_search.llm_next_item_predictor.t5.config import T5ModelConfig
from python_search.llm_next_item_predictor.llm_model import LLMModel
import torch


class T5Model(LLMModel):
    model = None
    def __init__(self, model=None):
        from transformers import T5Tokenizer

        self.tokenizer = T5Tokenizer.from_pretrained("t5-small")
        self.config = T5ModelConfig()
        self.model = model


    @staticmethod
    def load_trained_model():
        llm_model = T5Model()

        from transformers import T5ForConditionalGeneration, logging
        logging.set_verbosity_error()
        # Load the model
        from python_search.logger import setup_generic_stdout_logger

        logger = setup_generic_stdout_logger()

        logger.debug("Loading model from:" + llm_model.config.FULL_MODEL_PATH)
        model = T5ForConditionalGeneration.from_pretrained(
            llm_model.config.PRODUCTIONALIZED_MODEL
        )

        # Ensure the model is in evaluation mode
        model.eval()
        llm_model.model = model
        return  llm_model

    def predict(self, prompt, max_tokens=30) -> str:
        with torch.no_grad():
            inputs_tokenized = self.tokenizer.encode_plus(prompt, return_tensors="pt")
            input_ids = inputs_tokenized["input_ids"].to("cpu")
            attention_mask = inputs_tokenized["attention_mask"].to("cpu")

            # Generate prediction
            outputs = self.model.generate(
                input_ids=input_ids,
                attention_mask=attention_mask,
                max_new_tokens=max_tokens,
            )

            # Decode the prediction
            return self.tokenizer.decode(outputs[0], skip_special_tokens=True)
