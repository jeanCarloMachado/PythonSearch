import os


class LLMDataset:
    PROMPT_START = "predict the next key given this history: "
    DEFAULT_DATASET_SIZE = 3000

    def __init__(self, *, limit=DEFAULT_DATASET_SIZE):
        home = os.path.expanduser("~")
        self.DESTINATION = home + "/.python_search/dataset.pkl"
        self.limit = limit

    def generate(self):
        """
        Generates the dataset and writes it to disk
        """
        df = self.transform()
        print(f"Limiting to {df.limit} entries...")
        df = df.select("prompt", "label")
        df.show()
        df = df.toPandas()

        self.write(df)

    def transform(self):
        import pyspark.sql.functions as F

        df = self.base_data().filter("shortcut is NULL or shortcut != True")

        from pyspark.sql.functions import lag, concat_ws, lit, concat
        from pyspark.sql.window import Window

        windowSpec = Window.orderBy(
            "timestamp"
        )  # assuming "index" is the column that orders your data

        df = df.withColumn("previous_1", lag(df["key"]).over(windowSpec))
        df = df.withColumn("previous_2", lag(df["key"], 2).over(windowSpec))
        df = df.withColumn("previous_3", lag(df["key"], 3).over(windowSpec))

        df = df.withColumn("label", F.col("key"))
        df = df.withColumn(
            "prompt",
            concat(
                lit(self.PROMPT_START),
                concat_ws(",", "previous_1", "previous_2", "previous_3"),
            ),
        )

        df = df.limit(self.limit)
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
        print("Loading dataset with size", len(df.index))

        return df

    def _check_size(self):
        import subprocess

        return subprocess.check_output(
            "du -sh " + self.DESTINATION, shell=True, text=True
        )

    def base_data(self):
        from python_search.events.run_performed.dataset import EntryExecutedDataset

        data = EntryExecutedDataset().load_new()
        return data.sort("timestamp", ascending=False)

    def inspect_generated(self):
        return self.load().to_string()


def main():
    import fire

    fire.Fire(LLMDataset)


if __name__ == "__main__":
    main()
