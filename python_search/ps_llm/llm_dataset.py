import os
from typing import Literal

from python_search.ps_llm.tasks.classity_entry_type import ClassifyEntryType
from python_search.ps_llm.tasks.entry_title_generator import EntryTitleGenerator
from python_search.ps_llm.tasks.next_item_predictor import NextItemPredictor
from python_search.ps_llm.utils import timer


class LLMDataset:
    DATASET_VERSION = 'v7'
    VALIDATION_SIZE_TASK = 200
    MAX_DATASET_SIZE = 10000

    TASKS = [
        ClassifyEntryType,
        EntryTitleGenerator,
        NextItemPredictor
    ]

    def __init__(self):
        home = os.path.expanduser("~")
        self.BASE_FOLDER = home + f"/.python_search/datasets"
        self.DESTINATION_TRAIN = f"{self.BASE_FOLDER}/{self.DATASET_VERSION}_train.pkl"
        self.DESTINATION_VALIDATION = f"{self.BASE_FOLDER}/{self.DATASET_VERSION}_validation.pkl"
        print('Version: ', self.DATASET_VERSION)

    @timer
    def generate(self, save_to_disk=True):
        """
        Generates the dataset and writes it to disk
        """
        print("Train Dataset will be saved to: ", self.DESTINATION_TRAIN)
        print("Validation Dataset will be saved to: ", self.DESTINATION_VALIDATION)
        import pyspark.sql.functions as F
        from pyspark.sql import Window

        if not save_to_disk:
            print("Save to disk disabled")


        validation_set = None
        train_set = None
        for task in self.TASKS:

            task_instance = task()
            df_instance = task_instance.build_dataset()

            df_instance = df_instance.orderBy(F.rand())
            df_instance = df_instance.withColumn("order", F.lit("1"))
            w = Window().partitionBy(F.lit("order")).orderBy(F.lit("order"))
            df_instance = df_instance.withColumn("row_num", F.row_number().over(w))
            print("Rows for " + task.__name__ + ": " + str(df_instance.count()))


            validation_instance = df_instance.filter(df_instance.row_num <= self.VALIDATION_SIZE_TASK).select("prompt", "label")
            train_instance = df_instance.filter(df_instance.row_num > self.VALIDATION_SIZE_TASK).select("prompt", "label")


            if validation_set is not None:
                print("Joining validation set")
                validation_set  = validation_set.union(validation_instance)
                train_set = train_set.union(train_instance)
            else:
                validation_set = validation_instance
                train_set = train_instance


        print("Joined train set size: ", train_set.count())
        print("Joined validation set size: ", validation_set.count())


        if not save_to_disk:
            print("Not saving to disk")
            return

        self.write(validation_set, train_set)
        print("Generated dataset worked successfully")

    def write(self, validation, train):
        validation_df = validation.toPandas()
        print("Saving Validation set to:", self.DESTINATION_VALIDATION)
        print("Dataset rows:", len(validation_df.index))
        validation_df.to_pickle(self.DESTINATION_VALIDATION)


        print("Saving train dataset")
        train_df = train.toPandas()
        print("Saving Training set to:", self.DESTINATION_TRAIN)
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
