from python_search.ps_llm.tasks.base_task import BaseDataTask
from python_search.ps_llm.utils import get_spark
from python_search.search.entries_loader import EntriesLoader


class ClassifyEntryType(BaseDataTask):
    PROMPT_START = "Classify the entry type as one of (Snippet, Url, Cmd, File) in the following content: "

    def prompt(self, key, content):
        return f"{self.PROMPT_START} key={key} content={content}"

    def build_dataset(self):
        entries = EntriesLoader.load_privacy_neutral_only()

        result = []
        for entry in entries:
            type = entry.get_type_str()
            if type in ["callable"]:
                continue

            if type == "cli_cmd":
                type = "Cmd"

            type = type.capitalize()

            result.append((self.prompt(entry.key, entry.get_content_str()), type))

        df = get_spark().createDataFrame(result, ["prompt", "label"])
        print("Entry classifier base dataset size: " + str(df.count()))

        from python_search.ps_llm.llm_dataset import LLMDataset

        return df.limit(LLMDataset.MAX_SIZE_PER_TASK_TRAIN_DATASET)

    @staticmethod
    def start_with_model():
        from python_search.ps_llm.t5.t5_model import T5Model

        instance = ClassifyEntryType()
        model = T5Model.load_productionalized_model()
        instance.model = model

        return instance

    def classify(self, key, value):
        prompt = self.prompt(key, value)
        print("Prompt: " + prompt)
        result = self.model.predict(prompt)

        print("Classify entry type result: ")
        return result


if __name__ == "__main__":
    import fire

    fire.Fire(ClassifyEntryType)
