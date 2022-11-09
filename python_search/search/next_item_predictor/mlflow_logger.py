from typing import Optional

import mlflow

from python_search.config import DataConfig


def configure_mlflow(experiment_name: Optional[str] = None):
    """
    train the _model and log it to MLFlow
    """

    if not experiment_name:
        experiment_name = DataConfig.NEXT_ITEM_EXPERIMENT_NAME

    data = {
        "experiment_name": experiment_name,
        "tracking_uri": f"file:{DataConfig.MLFLOW_MODELS_PATH}"
    }

    print('MLFlow configuration:', data)

    mlflow.set_tracking_uri(data['tracking_uri'])
    mlflow.set_experiment(data['experiment_name'])

    return mlflow
