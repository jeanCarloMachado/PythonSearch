import pyspark.sql.functions as F
from pyspark.sql import DataFrame

from python_search.events.run_performed.dataset import EntryExecutedDataset


class TimesUsed:
    """
    Times used feature
    """

    def __init__(self):
        _df = EntryExecutedDataset().load_clean()
        self._df = (
            _df.groupBy("key")
            .agg(F.count("key").alias("times_used"))
            .sort("times_used", ascending=False)
        )
        self._pandas_df = self._df.toPandas()

    def get_dataframe(self) -> DataFrame:
        return self._df

    def get_value(self, key) -> int:

        result = self._pandas_df[self._pandas_df["key"] == key]

        if result is None or result.empty:
            return 0
        print(result)

        return result["times_used"].values[0]


if __name__ == "__main__":
    import fire

    fire.Fire(TimesUsed)
