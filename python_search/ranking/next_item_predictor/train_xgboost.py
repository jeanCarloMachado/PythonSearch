import matplotlib.pyplot as plt
import numpy as np
import xgboost as xgb
from sklearn.metrics import mean_absolute_error
from sklearn.model_selection import train_test_split

from python_search.config import DataConfig
from python_search.ranking.next_item_predictor.offline_evaluation import \
    OfflineEvaluation
from python_search.ranking.next_item_predictor.transform import Transform


class TrainXGBoost:
    def train_and_log(self, dataset):
        """
        train the model and log it to MLFlow
        """
        import mlflow

        mlflow.set_tracking_uri(f"file:{DataConfig.MLFLOW_MODELS_PATH}")
        # this creates a new experiment
        mlflow.set_experiment(DataConfig.NEXT_ITEM_EXPERIMENT_NAME)
        mlflow.xgboost.autolog()

        with mlflow.start_run():
            model, offline_evaluation = self.train(dataset)
            # mlflow.log_params(metrics)
            mlflow.log_params(offline_evaluation)

        return model, offline_evaluation

    def train(self, dataset):

        X_train, X_test, Y_train, Y_test = self._transform_and_split(dataset)

        X_test_p = X_test
        X_test = np.delete(X_test, 0, axis=1)
        X_train = np.delete(X_train, 0, axis=1)

        model = xgb.XGBRegressor(
            tree_method="hist",
            eval_metric=mean_absolute_error,
            objective="reg:squarederror",
            eval_set=[(X_train, Y_train), (X_test, Y_test)],
            booster="gblinear",
        )

        eval_set = [(X_train, Y_train), (X_test, Y_test)]
        model.fit(X_train, Y_train, eval_set=eval_set)

        self._evaluate_metrics(model)
        offline_evaluation = OfflineEvaluation().run(model, dataset, X_test_p)
        print(offline_evaluation)

        return model, offline_evaluation

    def _transform_and_split(self, dataset):

        X, Y = Transform().transform_train(dataset)

        X_train, X_test, Y_train, Y_test = train_test_split(
            X, Y, test_size=0.10, random_state=42
        )
        X_test = np.where(np.isnan(X_test), 0.5, X_test)
        Y_test = np.where(np.isnan(Y_test), 0.5, Y_test)
        Y_train = np.where(np.isnan(Y_train), 0.5, Y_train)
        X_train = np.where(np.isnan(X_train), 0.5, X_train)

        return X_train, X_test, Y_train, Y_test

    def _evaluate_metrics(self, model, display_metrics=False):

        results = model.evals_result()
        epochs = len(results["validation_0"]["rmse"])
        x_axis = range(0, epochs)
        fig, ax = plt.subplots()
        ax.plot(x_axis, results["validation_0"]["rmse"], label="Train")
        ax.plot(x_axis, results["validation_1"]["rmse"], label="Test")
        ax.legend()
        plt.ylabel("rmse")
        plt.title("XGBoost_training rmse")
        if display_metrics:
            plt.show()

        results = model.evals_result()
        epochs = len(results["validation_0"]["mean_absolute_error"])
        x_axis = range(0, epochs)
        fig, ax = plt.subplots()
        ax.plot(x_axis, results["validation_0"]["mean_absolute_error"], label="Train")
        ax.plot(x_axis, results["validation_1"]["mean_absolute_error"], label="Test")
        ax.legend()
        plt.ylabel("mae")
        plt.title("XGBoost_training mae")
        if display_metrics:
            plt.show()
