import pyspark.sql.functions as F
from pyspark.sql import DataFrame

from python_search.datasets.searchesperformed import SearchesPerformed


class TimesUsed:
    """ """

    def __init__(self):
        _df = SearchesPerformed().load()
        self._df = (
            _df.groupBy("key")
            .agg(F.count("key").alias("times_used"))
            .sort("times_used", ascending=False)
        )
        self._pandas_df = self._df.toPandas()

    def get_dataframe(self) -> DataFrame:
        return self._df

    def item_popularity(self, key) -> int:
        result = self._pandas_df[self._pandas_df["key"] == key]

        if result is None:
            return 0

        return result["times_used"].values[0]


if __name__ == "__main__":
    import fire

    fire.Fire(TimesUsed)
