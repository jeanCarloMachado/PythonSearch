from transformers import T5Tokenizer, T5ForConditionalGeneration


class T5ModelConfig:
    MODEL_DIRECTORY = 'my_model_directory'
    FULL_MODEL_PATH = '/Users/jean.machado/projects/PythonSearch/my_model_directory'


class T5Model:

    def __init__(self):
        self.tokenizer = T5Tokenizer.from_pretrained('t5-small')
        self.config = T5ModelConfig()

    def load_trained_model(self):
        # Load the model
        from python_search.logger import setup_generic_stdout_logger
        logger = setup_generic_stdout_logger()

        logger.debug("Loading model from:" + self.config.FULL_MODEL_PATH)
        model = T5ForConditionalGeneration.from_pretrained(self.config.FULL_MODEL_PATH)

        # Ensure the model is in evaluation mode
        model.eval()
        return model, self.tokenizer
