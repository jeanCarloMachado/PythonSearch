import os
from typing import Literal

from python_search.ps_llm.tasks.classity_entry_type import ClassifyEntryType
from python_search.ps_llm.tasks.entry_title_generator import EntryTitleGenerator
from python_search.ps_llm.tasks.next_item_predictor import NextItemPredictor


class LLMDataset:
    DATASET_VERSION = 'v6'
    PROMPT_START = "predict the next key given this history: "
    VALIDATION_SIZE = 600

    def __init__(self):
        home = os.path.expanduser("~")
        self.BASE_FOLDER = home + f"/.python_search/datasets"
        self.DESTINATION_TRAIN = f"{self.BASE_FOLDER}/{self.DATASET_VERSION}_train.pkl"
        self.DESTINATION_VALIDATION = f"{self.BASE_FOLDER}/{self.DATASET_VERSION}_validation.pkl"
        print('Version: ', self.DATASET_VERSION)
        print("Train Dataset will be saved to: ", self.DESTINATION_TRAIN)
        print("Validation Dataset will be saved to: ", self.DESTINATION_VALIDATION)

    def generate(self, save_to_disk=True):
        """
        Generates the dataset and writes it to disk
        """

        if not save_to_disk:
            print("Save to disk disabled")

        entry_classifier = ClassifyEntryType()
        df1 = entry_classifier.build_dataset()
        print("Count for task " + ClassifyEntryType.__name__ + ": " + str(df1.count()))


        entry_title = EntryTitleGenerator()
        df2 = entry_title.build_dataset()
        print("Count for task " + EntryTitleGenerator.__name__ + ": " + str(df2.count()))


        next_item = NextItemPredictor()
        df3 = next_item.build_dataset()
        print("Count for task " + NextItemPredictor.__name__ + ": " + str(df3.count()))


        df = df1.union(df2).union(df3)

        print("Size before filtering for null", df.count())
        df = df.filter("prompt is not NULL and label is not NULL")
        print("Size after filtering for null", df.count())

        import pyspark.sql.functions as F
        from pyspark.sql import Window

        df = df.orderBy(F.rand())
        df = df.withColumn("order", F.lit("1"))
        w = Window().partitionBy(F.lit("order")).orderBy(F.lit("order"))
        df = df.withColumn("row_num", F.row_number().over(w))

        validation_set = df.filter(df.row_num <= self.VALIDATION_SIZE).select("prompt", "label")
        train_set = df.filter(df.row_num > self.VALIDATION_SIZE).select("prompt", "label")

        if not save_to_disk:
            print("Not saving to disk")
            return

        self.write(validation_set, train_set)
        print("Generated dataset worked successfully")

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


    def sample(self, dataset: Literal['train', 'validation'] = 'validation'):
        if dataset == 'validation':
            df = self.load_validation()
        else:
            df = self.load_training()

        import pandas as pd

        def show_rows(df, nrows=20000):
            with pd.option_context("display.max_rows", nrows): print(df)

        return show_rows(df)

    def inspect(self):
        return len(self.load_training().index)





def main():
    import fire

    fire.Fire(LLMDataset)


if __name__ == "__main__":
    main()
