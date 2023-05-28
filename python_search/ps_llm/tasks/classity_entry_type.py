from python_search.ps_llm.tasks.base_task import BaseDataTask
from python_search.ps_llm.utils import get_spark
from python_search.search.entries_loader import EntriesLoader


class ClassifyEntryType(BaseDataTask):
    PROMPT_START = 'Classify the entry type as one of (Snippet, Url, Cmd, File) in the following content: '

    def prompt(self, key, content):
        return f"{self.PROMPT_START}: {key}, {content}"

    def build_dataset(self):
        entries = EntriesLoader.load_entry_list()

        result = []
        for entry in entries:
            type = entry.get_type_str()
            if type in ['callable']:
                continue

            if type == 'cli_cmd':
                type = 'Cmd'

            type = type.capitalize()

            result.append((self.prompt(entry.key, entry.get_content_str()), type))

        df = get_spark().createDataFrame(result, ["prompt", "label"])
        print("Entry classifier base dataset size: " + str(df.count()))

        return df.limit(5000)



if __name__ == "__main__":
    import fire
    fire.Fire(ClassifyEntryType)




