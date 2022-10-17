from python_search.config import DataConfig
import mlflow


def configure_mlflow():
    """
    train the _model and log it to MLFlow
    """


    mlflow.set_tracking_uri(f"file:{DataConfig.MLFLOW_MODELS_PATH}")
    # this creates a new experiment
    mlflow.set_experiment(DataConfig.NEXT_ITEM_EXPERIMENT_NAME)

    return mlflow