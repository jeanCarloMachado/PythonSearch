from typing import Optional

from mlflow.entities import RunInfo


class PythonSearchMLFlow:
    def get_latest_next_predictor_run(self, debug_info=False) -> RunInfo:
        import mlflow
        from mlflow.tracking import MlflowClient

        from search_run.config import DataConfig

        experiment_name = DataConfig.NEXT_ITEM_EXPERIMENT_NAME
        mlflow.set_tracking_uri(f"file:{DataConfig.MLFLOW_MODELS_PATH}")

        client: MlflowClient = MlflowClient()
        experiment = client.get_experiment_by_name(experiment_name)
        if debug_info:
            print(f"Experiment id: {experiment.experiment_id}")
        runs = client.list_run_infos(experiment_id=experiment.experiment_id)
        return runs[0]

    def get_next_predictor_model(self, run_id: Optional[str] = None, debug_info=False):
        import mlflow

        if not run_id:
            run_id = self.get_latest_next_predictor_run().run_id

        if debug_info:
            print(f"Loading run id: {run_id}")

        return mlflow.keras.load_model(f"runs:/{run_id}/model")
