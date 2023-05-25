from python_search.ps_llm.tasks.base_task import BaseDataTask
from python_search.search.entries_loader import EntriesLoader

def get_spark():
    from pyspark.sql.session import SparkSession

    return (
        SparkSession.builder.config("spark.executor.memory", "15g")
        .config("spark.driver.memory", "10g")
        .config("spark.memory.offHeap.enabled", True)
        .config("spark.memory.offHeap.size", "16g")
        .getOrCreate()
    )


class EntryTitleGenerator(BaseDataTask):
    PROMPT_START = 'Predict the title given for an entry with the following content'

    def prompt(self, content):
        return f"{self.PROMPT_START}: {content}"

    def build_dataset(self):

        keys, values = EntriesLoader.load_key_values_str()

        result = [ ]

        for i, key in enumerate(keys):
            row = (self.prompt(values[i]), key)
            result.append(row)

        df = get_spark().createDataFrame(result, ["prompt", "label"])

        return df.limit(4000)



if __name__ == "__main__":
    import fire
    fire.Fire(EntryTitleGenerator)




