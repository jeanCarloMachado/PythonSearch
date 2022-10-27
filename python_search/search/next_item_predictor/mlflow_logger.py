from typing import Optional

import mlflow

from python_search.config import DataConfig


def configure_mlflow(experiment_name: Optional[str] = None):
    """
    train the _model and log it to MLFlow
    """

    mlflow.set_tracking_uri(f"file:{DataConfig.MLFLOW_MODELS_PATH}")
    # this creates a new experiment
    if not experiment_name:
        experiment_name = DataConfig.NEXT_ITEM_EXPERIMENT_NAME

    mlflow.set_experiment(experiment_name)

    return mlflow
