from typing import List

import mlflow
import pyspark.sql.functions as F
import xgboost
from pyspark.sql.session import SparkSession
from sentence_transformers import SentenceTransformer
#%%
from xgboost import XGBRegressor

from search_run.core_entities import SearchRunPerformedType


def create_embeddings(keys: List[str]):
    transformer = SentenceTransformer('nreimers/MiniLM-L6-H384-uncased')
    return transformer.encode(keys, batch_size = 8, show_progress_bar=True)


def load_searches(path: str):
    """
    Loads the runs performed and extract some date features
    """
    spark = SparkSession.builder.getOrCreate()
    df : SearchRunPerformedType = spark.read.format("parquet").load(path)
    searches_df = df.filter("shortcut=False")
    searches_df = searches_df.withColumn('date', F.to_date("timestamp"))
    searches_df = searches_df.withColumn('week_day', F.dayofweek("timestamp"))
    searches_df = searches_df.withColumn('week_number', F.weekofyear("timestamp"))
    searches_df = searches_df.sort('date', ascending=False)
    return searches_df


def aggregate_searches(searches_df):
    """
    Aggregates the searches by key and week
    """
    count_key_df = searches_df.groupby('key', 'week_day','week_number')\
                    .agg(\
                         F.last('timestamp').alias('last_executed'),\
                         F.count('key').alias("times_executed")
                        )

    count_key_df = count_key_df.filter("key != 'search run search focus or open'")
    count_key_df = count_key_df.sort(['week_number' ,'week_day', 'times_executed'], ascending=False)
    return count_key_df


def train(X, Y):
    print("Version of xgboost: "  + xgboost.__version__)
    xgboost.set_config(verbosity=2)
    model: XGBRegressor = XGBRegressor(n_estimators=1000, max_depth=7, eta=0.1, subsample=0.7, colsample_bytree=0.8)
    model.fit(X, Y, verbose=True)
    return model


def compute_embeddings_current_keys():
    from entries.main import config

    current_keys = list(config.commands.keys())
    current_keys_embeddings = create_embeddings(current_keys)
    keys_embeddings = dict(zip(current_keys, current_keys_embeddings.tolist()))

    return keys_embeddings
