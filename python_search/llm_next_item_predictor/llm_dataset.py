import os

from python_search.events.run_performed.clean import RunPerformedCleaning


class LLMDataset:
    PROMPT_START = "predict the next key given this history: "
    DEFAULT_DATASET_SIZE = 3000
    DATASET_VERSION = 'v2'

    def __init__(self, *, limit=DEFAULT_DATASET_SIZE):
        home = os.path.expanduser("~")
        self.DESTINATION = home + f"/.python_search/datasets/{self.DATASET_VERSION}_train.pkl"
        print("Dataset destination:", self.DESTINATION)
        self.limit = limit

    def generate(self, save_to_disk=True, skip_clean=False):
        """
        Generates the dataset and writes it to disk
        """

        if not skip_clean:
            RunPerformedCleaning().clean()
        else:
            print("Skipping cleaning")


        df = self.transform()
        print(f"Limiting to {df.limit} entries...")
        df = df.select("prompt", "label")
        df.show()
        df = df.toPandas()

        if save_to_disk:
            self.write(df)
        else:
            print("Not saving to disk")

    def transform(self):
        import pyspark.sql.functions as F

        df = self.base_data().filter('shortcut != "True"')
        print(f"Dataset rows after filtering: {df.count()}")

        from pyspark.sql.functions import lag, concat_ws, lit, concat
        from pyspark.sql.window import Window

        windowSpec = Window.orderBy(
            "timestamp"
        )  # assuming "index" is the column that orders your data

        df = df.withColumn("previous_1", lag(df["key"]).over(windowSpec))
        df = df.withColumn("previous_2", lag(df["key"], 2).over(windowSpec))
        df = df.withColumn("previous_3", lag(df["key"], 3).over(windowSpec))
        df = df.withColumn("previous_4", lag(df["key"], 4).over(windowSpec))
        df = df.withColumn("previous_5", lag(df["key"], 5).over(windowSpec))

        from pyspark.sql.functions import udf, struct

        def build_prompt(row):
            prompt = f"{self.PROMPT_START} "

            if row['previous_1'] is not None:
                prompt += f" 1. {row['previous_1']}"
            if row['previous_2'] is not None:
                prompt += f" 2. {row['previous_2']}"
            if row['previous_3'] is not None:
                prompt += f" 3. {row['previous_3']}"
            if row['previous_4'] is not None:
                prompt += f" 4. {row['previous_4']}"
            if row['previous_5'] is not None:
                prompt += f" 5. {row['previous_5']}"

            return prompt

        udf_f = udf(build_prompt)
        df = df.withColumn('prompt', udf_f(struct([df[x] for x in df.columns])))
        df = df.withColumn("label", F.col("key"))

        df = df.limit(self.limit)
        print('After transform: ')
        df.show(n=3, truncate=False)

        breakpoint()
        return df

    def write(self, df):
        print("Saving to:", self.DESTINATION)
        print("Dataset rows:", len(df.index))
        df.to_pickle(self.DESTINATION)
        # print(self.inspect_generated())
        print("Dataset diesk size:")
        print(self._check_size())

    def load(self):
        """
        Loads the dataset from disk
        """
        import os

        home = os.path.expanduser("~")
        import pandas as pd

        path = home + "/.python_search/datasets/dataset_v1_train.plk"
        df = pd.read_pickle(path)
        print(f"Loading dataset from path {path} with {len(df.index)} rows")

        return df

    def _check_size(self):
        import subprocess

        return subprocess.check_output(
            "du -sh " + self.DESTINATION, shell=True, text=True
        )

    def base_data(self):
        from python_search.events.run_performed.dataset import EntryExecutedDataset

        data = EntryExecutedDataset().load_new()
        result = data.sort("timestamp", ascending=False)
        print(f"Sample of dataset rows: {result.count()}")
        result.show(n=3)

        return result

    def inspect_generated(self):
        return self.load().to_string()


def main():
    import fire

    fire.Fire(LLMDataset)


if __name__ == "__main__":
    main()
