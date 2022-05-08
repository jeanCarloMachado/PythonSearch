import datetime
import json
import logging
from typing import List

import mlflow
import numpy as np
from mlflow.entities import RunInfo
from mlflow.tracking import MlflowClient

from search_run.config import DataConfig
from search_run.infrastructure.redis import PythonSearchRedis


def get_ranked_keys(
    disable_cache=False, day_of_week=None, week_number=None
) -> List[str]:
    rank_cache = RankCache()
    rank = rank_cache.get_rank()
    if rank and not disable_cache:
        # logging.info('Using cached rank')
        return rank

    model = load_trained_model()

    keys_embeddings = load_precomputed_keys_embeddings()
    saved_keys = keys_embeddings.keys()
    embeddings = list(keys_embeddings.values())
    embeddings = np.array(embeddings)

    today_dataset = np.concatenate(
        (date_features(len(saved_keys), day_of_week, week_number), embeddings), axis=1
    )

    result = model.predict(today_dataset)
    result_with_key = list(zip(saved_keys, result))
    sorted_list = sorted(result_with_key, key=lambda x: x[1], reverse=True)
    ranked_list = [x[0] for x in sorted_list]

    rank_cache.update_cache(ranked_list)

    return ranked_list


def date_features(number_of_keys, day_of_week=None, week_number=None) -> np.ndarray:
    """
    generate the remaining date related features artifically, to be concatenated in teh final dataset for prediction

    """
    day_of_week = (
        day_of_week if day_of_week else datetime.datetime.today().isocalendar()[2]
    )
    week_number = (
        week_number if week_number else datetime.datetime.today().isocalendar()[1]
    )

    day_of_week_vec = np.full((number_of_keys, 1), day_of_week)
    week_number_vec = np.full((number_of_keys, 1), week_number)

    return np.concatenate((week_number_vec, day_of_week_vec), axis=1)


def load_trained_model():
    run = get_latest_run()
    logging.debug(f"RUn id: {run.run_id}")

    return mlflow.xgboost.load_model(f"runs:/{run.run_id}/model")


def load_precomputed_keys_embeddings():
    uri = get_latest_run().artifact_uri

    path = uri.replace("file://", "") + "/keys_embeddings.json"
    logging.debug(f"Path: {path}")
    with open(path, "r") as f:
        keys_embeddings = json.load(f)
    return keys_embeddings


def get_latest_run() -> RunInfo:
    """
    @todo use models/PythoSearchMlFlow abstraction instead
    """
    experiment_name = "baseline_rank_v0"
    mlflow.set_tracking_uri(f"file:{DataConfig.MLFLOW_MODELS_PATH}")

    client: MlflowClient = MlflowClient()
    experiment = client.get_experiment_by_name(experiment_name)
    logging.debug(f"Experiment id: {experiment.experiment_id}")
    runs = client.list_run_infos(experiment_id=experiment.experiment_id)

    return runs[0]


class RankCache:
    def __init__(self):
        self.redis = PythonSearchRedis.get_client()

    def clear(self):
        return self.redis.delete("cached_rank")

    def get_rank(self):
        result = self.redis.get("cached_rank")
        if result:
            return json.loads(result)

    def update_cache(self, ranked_list):
        self.redis.set("cached_rank", json.dumps(ranked_list))
