from typing import Tuple, Dict

import numpy as np
from pandas import DataFrame
from pyspark.sql import Window

from python_search.configuration.loader import ConfigurationLoader
from python_search.search.models import PythonSearchMLFlow
from python_search.next_item_predictor.features.entry_embeddings import InferenceEmbeddingsLoader
from python_search.next_item_predictor.features.entry_embeddings.entry_embeddings import \
    create_key_indexed_embedding
from python_search.next_item_predictor.model_interface import ModelInterface


class NextItemModelV2(ModelInterface):
    PRODUCTION_RUN_ID = "07c37a94ccb64c0c8e1eca195ad910cb"

    DIMENSIONS = 384 + 1

    def __init__(self):
        configuration = ConfigurationLoader().load_config()
        self._all_keys = configuration.commands.keys()
        self.inference_embeddings = InferenceEmbeddingsLoader(self._all_keys)

    def build_dataset(self) -> DataFrame:
        print("Building dataset v2")
        from python_search.events.ranking_generated import RankingGeneratedDataset
        import pyspark.sql.functions as F

        rg = RankingGeneratedDataset().load()
        rg = rg.withColumn("datetime", F.from_unixtime("timestamp"))

        base_entries = rg.select(F.posexplode("ranking").alias('position', 'entry'), "uuid", 'datetime').select("entry",
                                                                                                                "position",
                                                                                                                "uuid",
                                                                                                                "datetime")
        base_entries = base_entries.withColumn('executed', F.lit(0))

        # clean events
        from python_search.events.run_performed.dataset import EntryExecutedDataset

        performed_entries = EntryExecutedDataset().load_clean()
        performed_entries = performed_entries.filter("rank_uuid IS NOT NULL and rank_position IS NOT NULL").select(
            F.col("key").alias('entry'), F.col("rank_position").alias('position'), F.col("rank_uuid").alias('uuid'),
            F.col("timestamp").alias('datetime'))

        performed_entries = performed_entries.withColumn('executed', F.lit(1))
        unioned = base_entries.union(performed_entries)
        unioned = unioned.withColumn('timestamp', F.unix_timestamp('datetime'))
        unioned = unioned.withColumnRenamed("executed", "label")
        unioned = unioned.withColumnRenamed("entry", "key")


        window = Window.orderBy(F.col("key"))
        unioned = unioned.withColumn(
            "entry_number", F.row_number().over(window)
        )
        dataset = unioned.select('entry_number', 'key', 'datetime', 'timestamp', 'position', 'label')

        dataset.show(n=10, truncate=False)

        return dataset

    def transform_collection(
            self, dataset: DataFrame
    ) -> Tuple[np.ndarray, np.ndarray]:
        """
        Returns X and Y
        :param dataset:
        :return:
        """

        embeddings_keys = self._create_embeddings_training_dataset(dataset)
        # one extra for the row number
        X = np.zeros([dataset.count(), self.DIMENSIONS + 1])
        Y = np.empty(dataset.count())

        collected_rows = dataset.collect()
        #timestamp = dataset.select('timestamp').toPandas()['timestamp']
        #normalized_timestamp = self._NormalizeData(timestamp)

        for i, row in enumerate(collected_rows):
            X[i] = np.concatenate(
                [
                    # adds entry number so we can index and select the right row afterwards
                    # it gets deleted before training
                    np.asarray([row.entry_number]),
                    embeddings_keys[row.key],
                    np.asarray([row.timestamp])
                ]
            )

            Y[i] = row.label

        X = np.where(np.isnan(X), 0.5, X)
        Y = np.where(np.isnan(Y), 0.5, Y)

        return X, Y

    def _NormalizeData(self, data):
        """normalize a value between 0 and 1 """
        return (data - np.min(data)) / (np.max(data) - np.min(data))

    def load_mlflow_model(self):
        raise Exception("Not implemented")

    def transform_single(self, inference_input: dict) -> np.ndarray:
        """
        Return X
        :param inference_input:
        :return:
        """
        inference_input_obj = inference_input['inference_input']
        all_keys = inference_input['all_keys']
        from datetime import datetime;
        timestamp = int(datetime.now().timestamp())
        #timestamp_normalized = timestamp - 1669663110

        X = np.zeros([len(all_keys), self.DIMENSIONS])
        for i, key in enumerate(all_keys):
            key_embedding = self.inference_embeddings.get_embedding_from_key(key)
            if key_embedding is None:
                continue

            X[i] = np.concatenate(
                (
                    key_embedding,
                    np.asarray([timestamp])
                )
            )

        return X

    def load_mlflow_model(self, run_id=None):
        model = PythonSearchMLFlow().get_next_predictor_model(run_id=run_id)
        return model

    def get_run_id(self):
        return self.PRODUCTION_RUN_ID


    def _create_embeddings_training_dataset(
        self, dataset
    ) -> Dict[str, np.ndarray]:
        """
        create embeddings with all training keys and keep them in memory
        """
        print("Creating embeddings of training dataset")

        # add embeddings to the dataset
        collected_keys = dataset.select("key").collect()

        all_keys = []
        for collected_keys in collected_keys:
            all_keys.append(collected_keys.key)



        return create_key_indexed_embedding(all_keys)
