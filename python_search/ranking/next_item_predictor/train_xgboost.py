from typing import Any

import matplotlib.pyplot as plt
import xgboost as xgb
from sklearn.metrics import mean_absolute_error

Model = Any


class TrainXGBoost:
    def train(self, X_train, X_test, Y_train, Y_test) -> Model:

        model = xgb.XGBRegressor(
            tree_method="hist",
            eval_metric=mean_absolute_error,
            objective="reg:squarederror",
            eval_set=[(X_train, Y_train), (X_test, Y_test)],
            booster="gbtree",
            verbose=True,
        )

        eval_set = [(X_train, Y_train), (X_test, Y_test)]
        model.fit(X_train, Y_train, eval_set=eval_set)

        print("Xgboost was trained successfully!")
        return model

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
