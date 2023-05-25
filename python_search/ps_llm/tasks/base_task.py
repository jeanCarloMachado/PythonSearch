
class BaseDataTask:
    def prompt(self):
        raise NotImplementedError()

    def build_dataset(self):
        raise NotImplementedError()

    def predict(self, content):
        from python_search.ps_llm.t5.t5_model import T5Model
        from python_search.ps_llm.t5.config import T5ModelConfig

        model = T5Model.load_trained_model(T5ModelConfig.BASE_MODEL_PATH + '/model_v8_epoch_1')
        result = model.predict(self.prompt(content))

        print("Prediction result: ")
        return result
