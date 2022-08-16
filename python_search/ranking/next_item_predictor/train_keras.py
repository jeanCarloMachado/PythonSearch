import os
from typing import Any, Tuple

import mlflow
import numpy as np
from keras import layers
from keras.models import Sequential
from sklearn.model_selection import train_test_split

from python_search.config import DataConfig
from python_search.ranking.next_item_predictor.offline_evaluation import \
    OfflineEvaluation
from python_search.ranking.next_item_predictor.training_dataset import \
    TrainingDataset
from python_search.ranking.next_item_predictor.transform import Transform


class Train:
    EPOCHS = 30
    TEST_SPLIT_SIZE = 0.10
    BATCH_SIZE = 128

    def __init__(self, epochs=None):
        if not epochs:
            epochs = Train.EPOCHS
        self.epochs = epochs
        # enable the profiling scaffolding
        os.environ["TIME_IT"] = "1"

    def train_and_log(self, dataset):
        """
        train the model and log it to MLFlow
        """

        mlflow.set_tracking_uri(f"file:{DataConfig.MLFLOW_MODELS_PATH}")
        # this creates a new experiment
        mlflow.set_experiment(DataConfig.NEXT_ITEM_EXPERIMENT_NAME)
        mlflow.keras.autolog()
        # @todo: try mlflow.keras.autolog()

        with mlflow.start_run():
            model, metrics, offline_evaluation = self.train(dataset)
            mlflow.log_params(metrics)
            mlflow.log_params(offline_evaluation)

        return model, metrics, offline_evaluation

    def train(self, dataset: TrainingDataset, plot_history=False):
        """
        performs training

        :param dataset:
        :param plot_history:
        :return:
        """

        # prepare the data
        X, Y = Transform().transform_train(dataset)
        X_train, X_test, Y_train, Y_test = self.split(X, Y)

        X_test = np.where(np.isnan(X_test), 0.5, X_test)
        Y_test = np.where(np.isnan(Y_test), 0.5, Y_test)
        Y_train = np.where(np.isnan(Y_train), 0.5, Y_train)

        X_test_p = np.delete(X_test, 0, axis=1)
        X_train_p = np.delete(X_train, 0, axis=1)

        model, history = self._only_train(X_train_p, X_test_p, Y_train, Y_test)
        metrics = self._compute_standard_metrics(
            model, X_train_p, X_test_p, Y_train, Y_test
        )

        offline_evaluation = OfflineEvaluation().run(model, dataset, X_test)

        if plot_history:
            self._plot_training_history(history)

        return model, metrics, offline_evaluation

    def _only_train(self, X_train, X_test, Y_train, Y_test) -> Tuple[Any, Any]:

        print("Starting train with N epochs, N=", self.epochs)
        print(
            {
                "shape_x_train": X_train.shape,
                "shape_x_test": X_test.shape,
                "shape_y_train": Y_train.shape,
                "shape_y_test": Y_test.shape,
                "X_train has nan: ": np.any(np.isnan(X_train)),
                "Y_train has nan: ": np.any(np.isnan(Y_train)),
                "X_test has nan: ": np.any(np.isnan(X_test)),
                "y_test has nan: ": np.any(np.isnan(Y_test)),
            }
        )

        model = Sequential()
        model.add(layers.Dense(128, activation="relu"))
        model.add(layers.Dropout(0.5))
        model.add(layers.Dense(64, activation="relu"))
        model.add(layers.Dropout(0.5))
        model.add(layers.Dense(1))
        model.compile(optimizer="rmsprop", loss="mse", metrics=["mae", "mse"])

        history = model.fit(
            X_train,
            Y_train,
            epochs=self.epochs,
            batch_size=Train.BATCH_SIZE,
            validation_data=(X_test, Y_test),
        )

        return model, history

    def split(self, X, Y):
        X_train, X_test, Y_train, Y_test = train_test_split(
            X, Y, test_size=Train.TEST_SPLIT_SIZE, random_state=42
        )
        return X_train, X_test, Y_train, Y_test

    def _compute_standard_metrics(self, model, X_train, X_test, Y_train, Y_test):
        """
        computes mse and mae for train and test splits
        """
        train_mse, train_mae, train_mse2 = model.evaluate(X_train, Y_train)
        test_mse, test_mae, test_mse2 = model.evaluate(X_test, Y_test)

        metrics = {
            "train_mse": train_mse,
            "train_mae": train_mae,
            "test_mse": test_mse,
            "test_mae": test_mae,
        }
        print("Metrics:", metrics)

        return metrics

    def _plot_training_history(self, history):
        import matplotlib.pyplot as plt

        loss = history.history["loss"]
        val_loss = history.history["val_loss"]

        epochs_range = range(1, self.epochs + 1)
        plt.plot(epochs_range, loss, "bo", label="Training Loss")
        plt.plot(epochs_range, val_loss, "b", label="Validation Loss")
        plt.title("Training and validation loss")
        plt.xlabel("Epochs")
        plt.ylabel("Loss")
        plt.legend()
        plt.show()

    def _normalize(self, X_train, X_test):
        # normalize
        mean = X_train.mean(axis=0)
        X_train -= mean
        std = X_train.std(axis=0)
        X_train /= std

        X_test -= mean
        X_test /= std

        return X_train, X_test
