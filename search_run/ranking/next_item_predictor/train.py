import os
from typing import Dict, List, Tuple

import mlflow
import numpy as np

from search_run.config import DataConfig
from search_run.ranking.entry_embeddings import create_indexed_embeddings
from search_run.ranking.next_item_predictor.training_dataset import TrainingDataset


class Train:
    EPOCHS = 30
    TEST_SPLIT_SIZE = 0.10
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
        mlflow.autolog()
        # @todo: try mlflow.keras.autolog()

        with mlflow.start_run():
            model, metrics = self.train(dataset)
            mlflow.log_params(metrics)

        return model, metrics

    def train(self, dataset: TrainingDataset, plot_history=False):

        X, Y = self.create_XY(dataset)

        from sklearn.model_selection import train_test_split

        X_train, X_test, Y_train, Y_test = train_test_split(
            X, Y, test_size=Train.TEST_SPLIT_SIZE, random_state=42
        )

        X_train, X_test = self._normalize(X_train, X_test)

        # fill test dataset nans with 0.5s
        X_test = np.where(np.isnan(X_test), 0.5, X_test)
        Y_test = np.where(np.isnan(Y_test), 0.5, Y_test)

        from keras import layers
        from keras.models import Sequential

        print("Starting train with N epochs, N=", self.epochs)
        model = Sequential()
        model.add(layers.Dense(256, activation="relu"))
        model.add(layers.Dropout(0.5))
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

    def create_XY(self, dataset: TrainingDataset) -> Tuple[np.ndarray, np.ndarray]:
        """
        Transform the dataset into X and Y
        Returns a pair with X, Y
        """

        embeddings_keys = self.create_embeddings_training_dataset(dataset)

        # + 1 is for the month number
        dimensions_X = 2 * 384 + 1 + 1
        print(f"Dimensions of dataset = {dimensions_X}")
        X = np.zeros([dataset.count(), dimensions_X])
        Y = np.empty(dataset.count())

        print("X shape:", X.shape)

        collected_keys = dataset.select(*TrainingDataset.columns).collect()

        for i, collected_key in enumerate(collected_keys):
            X[i] = np.concatenate(
                [
                    embeddings_keys[collected_key.key],
                    embeddings_keys[collected_key.previous_key],
                    np.asarray([collected_key.month]),
                    np.asarray([collected_key.hour]),
                ]
            )
            Y[i] = collected_key.label
        print("Sample dataset:", X[0])

        return X, Y

    def create_embeddings_training_dataset(
        self, dataset: TrainingDataset
    ) -> Dict[str, np.ndarray]:
        """
        create embeddings
        """

        # add embeddings to the dataset
        all_keys = self._get_all_keys_dataset(dataset)

        return create_indexed_embeddings(all_keys)

    def _get_all_keys_dataset(self, dataset: TrainingDataset) -> List[str]:
        collected_keys = dataset.select("key", "previous_key").collect()

        keys = []
        for collected_keys in collected_keys:
            keys.append(collected_keys.key)
            keys.append(collected_keys.previous_key)

        return keys
