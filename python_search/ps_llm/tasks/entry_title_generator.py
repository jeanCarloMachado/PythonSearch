from python_search.ps_llm.tasks.base_task import BaseDataTask
from python_search.ps_llm.utils import get_spark
from python_search.search.entries_loader import EntriesLoader


class EntryTitleGenerator(BaseDataTask):
    PROMPT_START = 'Generate the title for an entry with the following content: '

    def prompt(self, content):
        return f"{self.PROMPT_START} {content}"

    def build_dataset(self):

        keys, values = EntriesLoader.load_key_values_str()

        result = []

        for i, key in enumerate(keys):
            row = (self.prompt(values[i]), key)
            result.append(row)

        df = get_spark().createDataFrame(result, ["prompt", "label"])

        from python_search.ps_llm.llm_dataset import LLMDataset
        return df.limit(LLMDataset.MAX_DATASET_SIZE)



if __name__ == "__main__":
    import fire
    fire.Fire(EntryTitleGenerator)




