

class T5ModelConfig:
    VERSION = 'v2'
    MODEL_DIRECTORY = 'p5_llm_models/' + VERSION
    BASE_MODEL_PATH = '/Users/jean.machado/projects/PythonSearch/'
    FULL_MODEL_PATH =  BASE_MODEL_PATH + MODEL_DIRECTORY
    PRODUCTIONALIZED_MODEL = '/Users/jean.machado/projects/PySearchEntries/p5_llm_models/v2_epoch_16'


class T5Model:

    def __init__(self):
        from transformers import T5Tokenizer
        self.tokenizer = T5Tokenizer.from_pretrained('t5-small')
        self.config = T5ModelConfig()

    def load_trained_model(self):
        from transformers import T5ForConditionalGeneration, logging
        logging.set_verbosity_error()
        # Load the model
        from python_search.logger import setup_generic_stdout_logger
        logger = setup_generic_stdout_logger()

        logger.debug("Loading model from:" + self.config.FULL_MODEL_PATH)
        model = T5ForConditionalGeneration.from_pretrained(self.config.PRODUCTIONALIZED_MODEL)

        # Ensure the model is in evaluation mode
        model.eval()
        return model, self.tokenizer
