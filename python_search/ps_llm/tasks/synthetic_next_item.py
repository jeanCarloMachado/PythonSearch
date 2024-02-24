import os

from python_search.ps_llm.tasks.base_task import BaseDataTask
from python_search.ps_llm.utils import get_spark


class SyntheticNextItemPredictor(BaseDataTask):
    DATA = [
        {"history": ["meditation"], "next": ["journaling"]},
        {"history": ["news"], "next": ["news"]},
        {"history": ["linkedin"], "next": ["arxiv"]},
        {"history": ["facebook"], "next": ["arxiv"]},
        {"history": ["edit"], "next": ["commit", "github"]},
    ]

    def prompt(self, row):
        result = "Predict the next reasonable keys given this history: " + " ".join(
            row["history"]
        )
        return result

    def build_dataset(self, skip_clean=False):
        prompted = [(self.prompt(row), self.label(row)) for row in self.DATA]

        spark = get_spark()
        df = spark.createDataFrame(prompted, ["prompt", "label"])

        return df

    def label(selfs, row):
        result = f"1. {row['next'][0]}"
        if len(row["next"]) >= 2:
            result += f" 2. {row['next'][1]}"
        if len(row["next"]) >= 3:
            result += f" 3. {row['next'][2]}"
        return result


if __name__ == "__main__":
    import fire

    fire.Fire(SyntheticNextItemPredictor)
