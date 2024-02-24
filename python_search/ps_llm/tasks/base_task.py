class BaseDataTask:
    PROMPT_START = None

    def prompt(self):
        raise NotImplementedError()

    def build_dataset(self):
        raise NotImplementedError()

    def predict(self, content):
        from python_search.ps_llm.t5.t5_model import T5Model

        model = T5Model.load_productionalized_model()
        prompt = self.prompt(content)
        print("Prompt: " + prompt)
        result = model.predict(prompt)

        print("Prediction result: ")
        return result
