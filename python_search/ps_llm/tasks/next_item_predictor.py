import os

from python_search.events.run_performed.clean import RunPerformedCleaning
from python_search.ps_llm.t5.next_item_prompt import PromptBuilder
from python_search.ps_llm.tasks.base_task import BaseDataTask


class NextItemPredictor(BaseDataTask):
    def prompt(self, history):
        return PromptBuilder().build_prompt_inference(history)

    def build_dataset(self, skip_clean=False):
        """
        Generates the dataset and writes it to disk
        """
        import pyspark.sql.functions as F
        from pyspark.sql import Window

        if skip_clean:
            print("Skipping cleaning")
        elif "DEV" in os.environ:
            print("Skipping clean due to DEV environment variable being set")
        else:
            RunPerformedCleaning().clean()

        return self._transform()

    def _transform(self):
        df = self._base_data().filter('shortcut != "True"')
        print(f"Dataset rows after filtering: {df.count()}")

        from pyspark.sql.functions import lag, lead
        from pyspark.sql.window import Window

        windowSpec = Window.orderBy(
            "timestamp"
        )  # assuming "index" is the column that orders your data

        df = df.withColumn("previous_1", lag(df["key"]).over(windowSpec))
        df = df.withColumn("previous_2", lag(df["key"], 2).over(windowSpec))
        df = df.withColumn("previous_3", lag(df["key"], 3).over(windowSpec))
        df = df.withColumn("previous_4", lag(df["key"], 4).over(windowSpec))
        df = df.withColumn("previous_5", lag(df["key"], 5).over(windowSpec))

        df = df.withColumn("next_2", lag(df["key"], 1).over(windowSpec))
        df = df.withColumn("next_3", lag(df["key"], 2).over(windowSpec))

        from pyspark.sql.functions import udf, struct

        udf_prompt = udf(PromptBuilder().build_prompt_for_spark)
        udf_label = udf(self._label)

        df = df.withColumn("prompt", udf_prompt(struct([df[x] for x in df.columns])))
        df = df.withColumn("label", udf_label(struct([df[x] for x in df.columns])))

        df = df.select("prompt", "label")
        df.show(n=10, truncate=False)

        from python_search.ps_llm.llm_dataset import LLMDataset

        return df.limit(LLMDataset.MAX_SIZE_PER_TASK_TRAIN_DATASET)

    def _label(selfs, row):
        result = f"1. {row['key']}"

        if row["next_2"] is not None:
            result += f" 2. {row['next_2']}"
        if row["next_3"] is not None:
            result += f" 3. {row['next_3']}"
        return result

    def _base_data(self):
        from python_search.events.run_performed.dataset import EntryExecutedDataset

        data = EntryExecutedDataset().load_new()
        result = data.sort("timestamp", ascending=False)
        print(f"Sample of dataset rows: {result.count()}")
        result.show(n=3)

        return result


if __name__ == "__main__":
    import fire

    fire.Fire(NextItemPredictor)
