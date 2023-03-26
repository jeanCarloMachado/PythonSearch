from typing import Optional

import mlflow

from python_search.configuration.data_config import DataConfig


def configure_mlflow(experiment_name: Optional[str] = None):
    """
    setts up an mlflow uri and experiment name
    """

    data_config = DataConfig()

    if not experiment_name:
        experiment_name = data_config.NEXT_ITEM_EXPERIMENT_NAME

    data = {
        "experiment_name": experiment_name,
        "tracking_uri": f"file:{data_config.MLFLOW_MODELS_PATH}",
    }

    print("MLFlow configuration:", data)

    mlflow.set_tracking_uri(data["tracking_uri"])
    mlflow.set_experiment(data["experiment_name"])

    return mlflow
