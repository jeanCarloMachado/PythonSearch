#!/usr/bin/env python
import logging
import sys

from pyspark.sql.session import SparkSession

from search_run.observability.logger import initialize_logging

initialize_logging()


class EndToEnd:
    def build_dataset(self):
        from search_run.datasets.searchesperformed import SearchesPerformed
        logging.basicConfig(level=logging.INFO, handlers=[logging.StreamHandler(sys.stdout)]),

        spark = SparkSession.builder.getOrCreate()
        df = SearchesPerformed(spark).load()

        df.sort('timestamp', ascending=False).show()

        # build pair dataset with label

        import pyspark.sql.functions as F
        from pyspark.sql.window import Window

        ## add literal column
        df = df.withColumn('tmp', F.lit('toremove'))
        window = Window.partitionBy('tmp').orderBy('timestamp')

        df = df.withColumn('row_number', F.row_number().over(window)).sort('timestamp', ascending=False)
        df = df.withColumn('previous_key', F.lag('key', 1, None).over(window)).sort('timestamp', ascending=False)

        pair = df.select("key", "previous_key", 'timestamp')

        grouped = pair.groupBy('key', 'previous_key').agg(F.count('previous_key').alias('times')).sort('key', 'times')
        grouped.cache()
        grouped.count()
        ## add the label
        dataset = grouped.withColumn('label', F.col('times') / F.sum('times').over(Window.partitionBy('key'))).orderBy \
            ('key')
        dataset = dataset.select('key',
                                 'previous_key',
                                 'label')
        dataset = dataset.filter("LENGTH(key) > 1")

        return dataset

    def baseline_mse(self, dataset):
        # naive approach of setting the same as input and output, used as baseline to measure the real model against
        from sklearn.metrics import mean_squared_error

        # apply only to the  ones with the same name in input and output
        # complete dataset 8k, with the same name in input and output 150
        naive = dataset.filter('key == previous_key').select('key', 'label').withColumn('baseline', F.lit(1))
        pd_naive = naive.select('label', 'baseline').toPandas()
        return mean_squared_error(pd_naive.label, pd_naive.baseline)

    def run(self):
        logging.info("End to end ranking")
        dataset = self.build_dataset()
        print("MSE baseline: ", self.baseline_mse(dataset))
        dataset.show(n=10)


if __name__ == "__main__":
    import fire

    fire.Fire(EndToEnd)
