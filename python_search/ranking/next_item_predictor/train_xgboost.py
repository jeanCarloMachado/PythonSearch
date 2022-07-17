import matplotlib.pyplot as plt
import numpy as np
import xgboost as xgb
from sklearn.metrics import mean_absolute_error
from sklearn.model_selection import train_test_split

from python_search.ranking.next_item_predictor.transform import Transform


class TrainXGBoost:
    def train(self, dataset):

        X_train, X_test, Y_train, Y_test = self._split(dataset)

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

        return model

    def _split(self, dataset):

        X, Y = Transform().transform(dataset)

        X_train, X_test, Y_train, Y_test = train_test_split(
            X, Y, test_size=0.10, random_state=42
        )
        X_test = np.where(np.isnan(X_test), 0.5, X_test)
        Y_test = np.where(np.isnan(Y_test), 0.5, Y_test)
        Y_train = np.where(np.isnan(Y_train), 0.5, Y_train)
        X_train = np.where(np.isnan(X_train), 0.5, X_train)

        X_test_p = np.delete(X_test, 0, axis=1)
        X_train_p = np.delete(X_train, 0, axis=1)
        return X_train_p, X_test_p, Y_train, Y_test

    def _evaluate_metrics(self, model):

        results = model.evals_result()
        epochs = len(results["validation_0"]["rmse"])
        x_axis = range(0, epochs)
        fig, ax = plt.subplots()
        ax.plot(x_axis, results["validation_0"]["rmse"], label="Train")
        ax.plot(x_axis, results["validation_1"]["rmse"], label="Test")
        ax.legend()
        plt.ylabel("rmse")
        plt.title("XGBoost_training rmse")
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
        plt.show()
