from typing import Optional

from python_search.ps_llm.llm_config import LLMConfig
from python_search.ps_llm.llm_model import LLMModel
import torch


class T5Model(LLMModel):
    model = None

    def __init__(self, *, logger=None):
        from python_search.logger import setup_generic_stdout_logger
        from transformers import T5Tokenizer

        self.config = LLMConfig()

        self.tokenizer = T5Tokenizer.from_pretrained(
            self.config.BASE_ORIGINAL_MODEL, model_max_length=512, legacy=True
        )
        if not logger:
            logger = setup_generic_stdout_logger()
        self.logger = logger

    @staticmethod
    def load_productionalized_model() -> LLMModel:
        return T5Model.load_trained_model(
            LLMConfig().SUMMARIZATION_PRODUCTIONALIZED_MODEL
        )

    @staticmethod
    def load_trained_model(model_path: Optional[str] = None) -> LLMModel:
        llm_model = T5Model()

        from transformers import T5ForConditionalGeneration, logging

        logging.set_verbosity_error()
        # Load the model

        if not model_path:
            model_path = llm_model.config.NEXT_ITEM_PRODUCTIONALIZED_MODEL

        llm_model.logger.debug("Loading model from:" + model_path)
        model = T5ForConditionalGeneration.from_pretrained(model_path)

        # Ensure the model is in evaluation mode
        model.eval()
        llm_model.model = model
        return llm_model

    def predict(self, prompt, max_tokens=30, predict_device="cpu") -> str:
        # @todo consider moving prediction to the metal
        with torch.no_grad():
            inputs_tokenized = self.tokenizer.encode_plus(prompt, return_tensors="pt")
            input_ids = inputs_tokenized["input_ids"].to(predict_device)
            attention_mask = inputs_tokenized["attention_mask"].to(predict_device)
            self.model.to(predict_device)

            # Generate prediction
            outputs = self.model.generate(
                input_ids=input_ids,
                attention_mask=attention_mask,
                max_new_tokens=max_tokens,
            )

            # Decode the prediction
            return self.tokenizer.decode(outputs[0], skip_special_tokens=True)
