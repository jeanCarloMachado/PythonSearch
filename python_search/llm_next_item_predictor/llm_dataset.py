import os

from python_search.events.run_performed.clean import RunPerformedCleaning


class LLMDataset:
    PROMPT_START = "predict the next key given this history: "
    DEFAULT_DATASET_SIZE = 3000
    DATASET_VERSION = 'v2'
    VALIDATION_SIZE = 500


    def __init__(self, *, limit=DEFAULT_DATASET_SIZE):
        home = os.path.expanduser("~")
        self.BASE_FOLDER = home + f"/.python_search/datasets"
        self.DESTINATION_TRAIN = f"{self.BASE_FOLDER}/{self.DATASET_VERSION}_train.pkl"
        self.DESTINATION_VALIDATION = f"{self.BASE_FOLDER}/{self.DATASET_VERSION}_validation.pkl"
        print("Train Dataset will be saved to: ", self.DESTINATION_TRAIN)
        print("Validation Dataset will be saved to: ", self.DESTINATION_VALIDATION)
        self.limit = limit

    def generate(self, save_to_disk=True, skip_clean=False):
        """
        Generates the dataset and writes it to disk
        """
        import pyspark.sql.functions as F
        from pyspark.sql import Window

        if not skip_clean:
            RunPerformedCleaning().clean()
        else:
            print("Skipping cleaning")


        df = self.transform()

        df = df.orderBy(F.rand())

        df = df.withColumn("order", F.lit("1"))
        w = Window().partitionBy(F.lit("order")).orderBy(F.lit("order"))
        df = df.withColumn("row_num", F.row_number().over(w))

        validation_set = df.filter(df.row_num <= self.VALIDATION_SIZE).select("prompt", "label")
        train_set = df.filter(df.row_num > self.VALIDATION_SIZE).select("prompt", "label")

        if save_to_disk:
            self.write(validation_set, train_set)
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


        udf_f = udf(PromptBuilder().build_prompt_for_spark)
        df = df.withColumn('prompt', udf_f(struct([df[x] for x in df.columns])))
        df = df.withColumn("label", F.col("key"))

        df = df.limit(self.limit)
        print('After transform: ')
        df = df.select("prompt", "label")
        df.show(n=3, truncate=False)

        return df

    def write(self, validation, train):
        print("Saving validation dataset")
        validation_df = validation.toPandas()
        print("Saving to:", self.DESTINATION_VALIDATION)
        print("Dataset rows:", len(validation_df.index))
        validation_df.to_pickle(self.DESTINATION_VALIDATION)


        print("Saving train dataset")
        train_df = train.toPandas()
        print("Saving to:", self.DESTINATION_TRAIN)
        print("Dataset rows:", len(train_df.index))
        train_df.to_pickle(self.DESTINATION_TRAIN)


    def load(self):
        return self.load_training()

    def load_training(self):
        """
        Loads the dataset from disk
        """
        import os

        home = os.path.expanduser("~")
        import pandas as pd

        path = home + f"/.python_search/datasets/{self.DATASET_VERSION}_train.pkl"
        df = pd.read_pickle(path)
        print(f"Loading dataset from path {path} with {len(df.index)} rows")
        return df


    def load_validation(self):
        """
        Loads the dataset from disk
        """
        import os

        home = os.path.expanduser("~")
        import pandas as pd

        path = home + f"/.python_search/datasets/{self.DATASET_VERSION}_validation.pkl"
        df = pd.read_pickle(path)
        print(f"Loading dataset from path {path} with {len(df.index)} rows")
        return df

    def base_data(self):
        from python_search.events.run_performed.dataset import EntryExecutedDataset

        data = EntryExecutedDataset().load_new()
        result = data.sort("timestamp", ascending=False)
        print(f"Sample of dataset rows: {result.count()}")
        result.show(n=3)

        return result

    def inspect_generated(self):
        return self.load().to_string()

class PromptBuilder:
    PROMPT_START = "predict the next key given this history: "

    def build_prompt_inference(self, history):
        prompt = f"{self.PROMPT_START} "

        for i in range(0, len(history)):

            prompt += f" {i+1}. {history[i]}"
            if i > 5:
                break

        return prompt

    def build_prompt_for_spark(self, row):
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


def main():
    import fire

    fire.Fire(LLMDataset)


if __name__ == "__main__":
    main()
