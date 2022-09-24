import pyspark.sql.functions as F
from python_search.datasets.searchesperformed import SearchesPerformed

class GlobalPopularity:
    def __init__(self):
        _df = SearchesPerformed().load()
        _df = _df.groupBy('key').agg(F.count('key').alias('times_used')).sort('times_used', ascending=False)
        self._pandas_df = _df.toPandas()

    def item_popularity(self, key) -> int:
        return self._pandas_df[self._pandas_df['key'] == key]['times_used'].values[0]

if __name__ == '__main__':
    import fire
    fire.Fire(GlobalPopularity)
