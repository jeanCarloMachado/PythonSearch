import os
from typing import Literal, Optional

from mlflow.entities import RunInfo

from python_search.config import DataConfig


class PythonSearchMLFlow:
    """
    Accessor to MLflow API

    """

    def __init__(self):

        self.debug = os.getenv("PS_DEBUG", False)
        import mlflow

        self.mlflow_instance = mlflow
        self.mlflow_instance.set_tracking_uri(f"file:{DataConfig.MLFLOW_MODELS_PATH}")

    def get_latest_next_predictor_run(self) -> RunInfo:
        from mlflow.tracking import MlflowClient

        experiment_name = DataConfig.NEXT_ITEM_EXPERIMENT_NAME

        client: MlflowClient = MlflowClient()
        experiment = client.get_experiment_by_name(experiment_name)
        if self.debug:
            print(f"Experiment id: {experiment.experiment_id}")
        runs = client.list_run_infos(experiment_id=experiment.experiment_id)
        return runs[0]

    def get_next_predictor_model(self, run_id: Optional[str] = None):
        from typing import Literal

        model_type: Literal["xgboost", "keras"] = "xgboost"

        if not run_id:
            run_id = self.get_latest_next_predictor_run().run_id

        if self.debug:
            print(f"Loading run id: {run_id}")

        if model_type == "keras":
            model = self.mlflow_instance.keras.load_model(f"runs:/{run_id}/model")
        else:
            model = self.mlflow_instance.xgboost.load_model(f"runs:/{run_id}/model")

        return model
