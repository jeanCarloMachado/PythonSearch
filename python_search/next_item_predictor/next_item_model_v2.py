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

def number_of_same_words(key1, key2):
    count = 0
    for i in key1.split(' '):
        for j in key2.split(' '):
            if i == j:
                count+=1
    return count

def number_of_same_words_from_row(row):
    return number_of_same_words(row['key_performed'], row['key'])

class NextItemModelV2(ModelInterface):
    PRODUCTION_RUN_ID = "ab9c5ed3eabb46ef8216314e55646ea6"

    DIMENSIONS = 384 + 1

    def __init__(self):
        configuration = ConfigurationLoader().load_config()
        self._all_keys = configuration.commands.keys()
        self.inference_embeddings = InferenceEmbeddingsLoader(self._all_keys)

    def build_dataset(self, debug=True) -> DataFrame:
        import pyspark.sql.functions as F

        print("Building dataset v2")

        ranking_df = self._get_ranking_entries_dataset()
        print(f'Rank entries total: {ranking_df.count()}')


        performed_df = self._get_performed_entries_dataset()
        performed_df = performed_df.withColumn('share_words_count', F.lit(0))

        # decrement the position of the performed entries, it starts at 1 there but at the ranking event at 0
        print('Decrementing performed entries position')

        performed_df = performed_df.withColumn('position', F.col('position').cast('int'))
        performed_df = performed_df.withColumn('position', F.col('position') - 1)
        performed_df = performed_df.withColumn('position', F.col('position').cast('String'))


        # remove ranks without performed keys in it
        performed_uuids = performed_df.select('uuid').withColumnRenamed('uuid', 'performed_uuid')


        ranking_df = performed_uuids.join(ranking_df, on=performed_uuids.performed_uuid == ranking_df.uuid, how='left')
        ranking_df = ranking_df.drop('performed_uuid')
        ranking_df = ranking_df.withColumn('position', F.col('position').cast('int'))
        print(f'Ranks entries with executed item: {ranking_df.count()}')


        # remove entries that contain the performed key

        performed_keys = performed_df.select(F.col('key').alias('performed_key'), F.col('uuid').alias('performed_uuid'),
                                             F.col('position').alias('performed_position'))

        ranking_df = ranking_df.join(performed_keys, on=[ performed_keys.performed_uuid == ranking_df.uuid,
                                                     performed_keys.performed_position == ranking_df.position],
                                 how='left_anti')




        ## add number of same words as feature
        performed_key_and_uuid = performed_df.select(F.col('uuid').alias('uuid_performed'), F.col('key').alias('key_performed'))
        same_words_df = performed_key_and_uuid.join(ranking_df, on=performed_key_and_uuid.uuid_performed == ranking_df.uuid, how='left')
        from pyspark.sql.functions import udf, struct
        udf_f = udf(number_of_same_words_from_row)
        same_words_df = same_words_df.withColumn('share_words_count', udf_f(struct([same_words_df[x] for x in same_words_df.columns])))
        ranking_df = same_words_df.drop('uuid_performed').drop('key_performed')

        # add same words as criteria for label
        ranking_df = ranking_df.withColumn('label', F.when(F.col('share_words_count') > 0, 2).otherwise(F.col('label')))

        ranking_df.printSchema()
        performed_df.printSchema()

        unioned = ranking_df.union(performed_df)
        unioned = unioned.withColumn('timestamp', F.unix_timestamp('datetime'))


        window = Window.orderBy(F.col("key"))
        unioned = unioned.withColumn(
            "entry_number", F.row_number().over(window)
        )

        # prepare result for returning
        # select only relevant columns
        dataset = unioned.select('entry_number',  'key', 'uuid', 'datetime', 'timestamp', 'position', 'label')
        # sort dataframe in a readable way
        dataset = dataset.sort(['uuid', 'timestamp', 'position'], ascending=[True, False, True])


        if debug:
            dataset.show(n=10, truncate=False)

        return dataset

    def _get_ranking_entries_dataset(self) -> DataFrame:
        """
        Returns the ranking generated data in the format of the base dataset
        :return:
        """
        import pyspark.sql.functions as F
        from python_search.events.ranking_generated import RankingGeneratedDataset
        rg = RankingGeneratedDataset().load()
        rg = rg.withColumn("datetime", F.from_unixtime("timestamp"))

        base_entries = rg.select(F.posexplode("ranking").alias('position', 'entry'), "uuid", 'datetime').select(F.col("entry").alias('key'),
                                                                                                                "position",
                                                                                                                "uuid",
                                                                                                                "datetime")
        # entries form ranking generated by default contain not executed things
        return base_entries.withColumn('label', F.lit(0))

    def _get_performed_entries_dataset(self) -> DataFrame:
        from python_search.events.run_performed.dataset import EntryExecutedDataset
        import pyspark.sql.functions as F
        performed_entries = EntryExecutedDataset().load_clean()
        performed_entries = performed_entries.filter("rank_uuid IS NOT NULL and rank_position IS NOT NULL").select(
            F.col("key"), F.col("rank_position").alias('position'), F.col("rank_uuid").alias('uuid'),
            F.col("timestamp").alias('datetime'))
        return performed_entries.withColumn('label', F.lit(5))

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

        X = np.zeros([len(all_keys), self.DIMENSIONS])
        for i, key in enumerate(all_keys):
            key_embedding = self.inference_embeddings.get_embedding_from_key(key)
            if key_embedding is None:
                print(f"No embeddings for key: '{key}'")
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
