import datetime
import logging
import os
from typing import List

import mlflow
import numpy as np
import pyspark.sql.functions as F
import xgboost
from pyspark.sql.session import SparkSession
from sentence_transformers import SentenceTransformer
from sklearn.metrics import mean_squared_error as MSE
from sklearn.model_selection import train_test_split
from xgboost import XGBRegressor

from search_run.core_entities import SearchRunPerformedType
from search_run.ranking.pipeline.ml_based import get_latest_run, get_ranked_keys

home = os.getenv("HOME")
path = "/data/python_search/data_warehouse/dataframes/SearchRunPerformed"
location = f"{home}/projects/PySearchEntries/mlflow"
experiment_name = "baseline_rank_v0"


def load_searches():
    """
    Loads the runs performed and extract some date features
    """
    spark = SparkSession.builder.getOrCreate()
    df: SearchRunPerformedType = spark.read.format("parquet").load(path)
    searches_df = df.filter("shortcut=False")
    searches_df = searches_df.withColumn("date", F.to_date("timestamp"))
    searches_df = searches_df.withColumn("week_day", F.dayofweek("timestamp"))
    searches_df = searches_df.withColumn("week_number", F.weekofyear("timestamp"))
    searches_df = searches_df.sort("date", ascending=False)
    return searches_df


def aggregate_searches(searches_df):
    """
    Aggregates the searches by key and week
    """
    count_key_df = searches_df.groupby("key", "week_day", "week_number").agg(
        F.last("timestamp").alias("last_executed"),
        F.count("key").alias("times_executed"),
    )

    count_key_df = count_key_df.filter("key != 'search run search focus or open'")
    count_key_df = count_key_df.sort(
        ["week_number", "week_day", "times_executed"], ascending=False
    )
    return count_key_df


def create_dataset(aggreagted_df):
    # setup the rest of the dataset and merge them
    X = aggreagted_df.select("week_number", "week_day").toPandas().to_numpy()
    return np.concatenate((X, create_historical_embeddings(aggreagted_df)), axis=1)


def create_Y(aggregated_df):
    Y = aggregated_df.select("times_executed").collect()
    Y = [yi.times_executed for yi in Y]
    return Y


def perform_train_and_log(keys_embeddings, X, Y):
    mlflow.set_tracking_uri(f"file:{location}")
    # this creates a new experiment
    mlflow.set_experiment(experiment_name)
    mlflow.autolog()
    import logging

    with mlflow.start_run():
        # Splitting
        test_size = 0.1
        train_X, test_X, train_y, test_y = train_test_split(
            X, Y, test_size=test_size, random_state=223
        )

        # train model
        mlflow.log_params({"dataset_size": len(X), "test_size_percentage": test_size})

        xgboost.set_config(verbosity=2)
        # eta  = learning rate
        # max_depth = controls overfitting default=6
        # n_estimators: 100 if the size of your data is high, 1000 is if it is medium-low
        model: XGBRegressor = XGBRegressor(
            n_estimators=100, max_depth=7, eta=0.1, subsample=0.7, colsample_bytree=0.8
        )
        model.fit(train_X, train_y, verbose=True)
        mlflow.xgboost.log_model(xgb_model=model, artifact_path="model")

        logging.info("Fitting is over")

        pred_train = model.predict(train_X)
        pred_validation = model.predict(test_X)
        # RMSE Computation
        rmse = {
            "rmse_train": np.sqrt(MSE(train_y, pred_train)),
            "rmse_validation": np.sqrt(MSE(test_y, pred_validation)),
        }
        print(rmse)

        mlflow.log_params(rmse)

        # precompute the current keys embeddings and save them in mlflow
        # so we can load them later to produce the predictions without hurting performance

        mlflow.log_dict(keys_embeddings, "keys_embeddings.json")
        mlflow.end_run()

    print(f"End at {datetime.datetime.now().isoformat()}")


def compute_embeddings_current_keys():
    from entries.main import config

    current_keys = list(config.commands.keys())
    current_keys_embeddings = create_embeddings(current_keys)
    keys_embeddings = dict(zip(current_keys, current_keys_embeddings.tolist()))

    return keys_embeddings


def create_historical_embeddings(aggregated_df):
    # setup the embeddings of the old executed keys
    historical_train_keys = aggregated_df.select("key").collect()
    historical_train_keys = [key.key for key in historical_train_keys]
    return create_embeddings(historical_train_keys)


def create_embeddings(keys: List[str]):
    transformer = SentenceTransformer("nreimers/MiniLM-L6-H384-uncased")
    return transformer.encode(keys, batch_size=8, show_progress_bar=True)


def validate_latest_model_ranks():
    import pandas as pd

    run = get_latest_run()
    trained_time = datetime.datetime.fromtimestamp(run.start_time / 1000).strftime(
        "%Y-%m-%d %H:%M:%S.%f"
    )
    logging.info(f"Run id: {run.run_id}, trained: {trained_time}")
    next_week = datetime.datetime.today().isocalendar()[1] + 1

    monday = get_ranked_keys(disable_cache=True, week_number=next_week, day_of_week=1)
    thursday = get_ranked_keys(disable_cache=True, week_number=next_week, day_of_week=4)
    saturday = get_ranked_keys(disable_cache=True, week_number=next_week, day_of_week=6)
    sunday = get_ranked_keys(disable_cache=True, week_number=next_week, day_of_week=7)

    df = pd.DataFrame(
        zip(monday, thursday, saturday, sunday),
        columns=["monday", "thursday", "saturday", "sunday"],
    )
    return df
