import os
import mlflow
import numpy as np

from search_run.config import DataConfig
from sklearn.model_selection import train_test_split
from search_run.ranking.next_item_predictor.training_dataset import TrainingDataset
from search_run.ranking.next_item_predictor.transform import Transform


class Train:
    EPOCHS = 20
    TEST_SPLIT_SIZE = 0.20
    BATCH_SIZE = 128

    def __init__(self, epochs=None):
        if not epochs:
            epochs = Train.EPOCHS
        self.epochs = epochs
        # enable the profiling scafolding
        os.environ["TIME_IT"] = "1"

    def train_and_log(self, dataset):
        """train the model and log it to MLFlow"""

        mlflow.set_tracking_uri(f"file:{DataConfig.MLFLOW_MODELS_PATH}")
        # this creates a new experiment
        mlflow.set_experiment(DataConfig.NEXT_ITEM_EXPERIMENT_NAME)
        mlflow.keras.autolog()
        # @todo: try mlflow.keras.autolog()

        with mlflow.start_run():
            model, metrics = self.train(dataset)
            mlflow.log_params(metrics)

        return model, metrics

    def split(self, X, Y):
        X_train, X_test, Y_train, Y_test = train_test_split(
            X, Y, test_size=Train.TEST_SPLIT_SIZE, random_state=42
        )
        return X_train, X_test, Y_train, Y_test


    def train(self, dataset: TrainingDataset, plot_history=False):

        X, Y = Transform().transform(dataset)
        X_train, X_test, Y_train, Y_test = self.split(X, Y)

        # fill test dataset nans with 0.5s
        X_test = np.where(np.isnan(X_test), 0.5, X_test)
        Y_test = np.where(np.isnan(Y_test), 0.5, Y_test)

        from keras import layers
        from keras.models import Sequential

        print("Starting train with N epochs, N=", self.epochs)
        model = Sequential()
        model.add(layers.Dense(64, activation="relu"))
        model.add(layers.Dense(1))
        model.compile(optimizer="rmsprop", loss="mse", metrics=["mae", "mse"])

        history = model.fit(
            X_train,
            Y_train,
            epochs=self.epochs,
            batch_size=Train.BATCH_SIZE,
            validation_data=(X_test, Y_test),
        )

        train_mse, train_mae, train_mse2 = model.evaluate(X_train, Y_train)
        test_mse, test_mae, test_mse2 = model.evaluate(X_test, Y_test)

        metrics = {
            "train_mse": train_mse,
            "train_mae": train_mae,
            "test_mse": test_mse,
            "test_mae": test_mae,
        }

        print("Metrics:", metrics)

        if plot_history:
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

        return model, metrics


    def _normalize(self, X_train, X_test):
        # normalize
        mean = X_train.mean(axis=0)
        X_train -= mean
        std = X_train.std(axis=0)
        X_train /= std

        X_test -= mean
        X_test /= std

        return X_train, X_test

