from transformers import T5Tokenizer, T5ForConditionalGeneration


class T5ModelConfig:
    MODEL_DIRECTORY = 'my_model_directory'


class T5Model:

    def __init__(self):
        self.tokenizer = T5Tokenizer.from_pretrained('t5-small')
        self.config = T5ModelConfig()

    def load_trained_model(self):
        # Load the model
        print("Loading model from:", self.config.MODEL_DIRECTORY)
        model = T5ForConditionalGeneration.from_pretrained(self.config.MODEL_DIRECTORY)

        # Ensure the model is in evaluation mode
        model.eval()
        return model, self.tokenizer
