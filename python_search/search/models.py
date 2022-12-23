import os
from typing import Literal, Optional

from mlflow.entities import RunInfo

from python_search.config import DataConfig

BASE_MLFLOW_LOCATON = "/entries/mlflow"

NEXT_ITEM_PREDICTOR_PROJECT_NUMBER = "2"
ENTRY_TYPE_CLASSIFIER_PROJECT_NUMBER = "4"
ENTRY_DESCRIPTION_GENERATOR_PROJECT_NUMBER = "5"


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
        # model_type: Literal["xgboost", "keras"] = "keras"

        if not run_id:
            run_id = self.get_latest_next_predictor_run().run_id

        if self.debug:
            print(f"Loading run id: {run_id}")

        path = f"{BASE_MLFLOW_LOCATON}/{NEXT_ITEM_PREDICTOR_PROJECT_NUMBER}/{run_id}/artifacts/model"

        if model_type == "keras":
            model = self.mlflow_instance.keras.load_model(path)
        else:
            model = self.mlflow_instance.xgboost.load_model(path)

        return model

    def get_entry_type_classifier(self, run_id):
        return self.mlflow_instance.keras.load_model(
            f"{BASE_MLFLOW_LOCATON}/{ENTRY_TYPE_CLASSIFIER_PROJECT_NUMBER}/{run_id}/artifacts/model"
        )

    def get_entry_description_geneartor(self, run_id):
        return self.mlflow_instance.keras.load_model(
            f"{BASE_MLFLOW_LOCATON}/{ENTRY_DESCRIPTION_GENERATOR_PROJECT_NUMBER}/{run_id}/artifacts/model"
        )

    def get_entry_description_geneartor_dict(self, run_id):
        return self.mlflow_instance.artifacts.load_dict(
            f"{BASE_MLFLOW_LOCATON}/{ENTRY_DESCRIPTION_GENERATOR_PROJECT_NUMBER}/{run_id}/artifacts/chars"
        )
