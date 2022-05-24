from typing import Dict, List, Tuple

import mlflow
import numpy as np

from search_run.config import DataConfig
from search_run.ranking.entry_embeddings import create_indexed_embeddings
from search_run.ranking.next_item_predictor.training_dataset import TrainingDataset


class Train:
    # looks like the ideal in the current architecture
    EPOCHS = 22

    def __init__(self, epochs=None):
        if not epochs:
            epochs = Train.EPOCHS
        self.epochs = epochs

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
            X, Y, test_size=0.20, random_state=42
        )

        # normalize
        mean = X_train.mean(axis=0)
        X_train -= mean
        std = X_train.std(axis=0)
        X_train /= std

        X_test -= mean
        X_test /= std

        from keras import layers
        from keras.models import Sequential

        print("Starting train with N epochs, N= ", self.epochs)
        model = Sequential()
        model.add(layers.Dense(100, activation="relu", input_shape=X[1].shape))
        model.add(layers.Dropout(0.5))
        model.add(layers.Dense(1))
        model.compile(optimizer="rmsprop", loss="mse", metrics=["mae"])

        history = model.fit(
            X_train,
            Y_train,
            epochs=self.epochs,
            batch_size=32,
            validation_data=(X_test, Y_test),
        )

        train_mse, train_mae = model.evaluate(X_train, Y_train)
        test_mse, test_mae = model.evaluate(X_test, Y_test)

        metrics = {
            "train_mse": train_mse,
            "train_mae": train_mae,
            "test_mse": test_mse,
            "test_mae": test_mae,
        }
        import pprint

        pprint.pprint(metrics)

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

    def create_XY(self, dataset: TrainingDataset) -> Tuple[np.ndarray, np.ndarray]:
        """
        Transform the dataset into X and Y
        Returns a pair with X, Y
        """

        embeddings_keys = self.create_embeddings_training_dataset(dataset)

        # + 1 is for the month number
        X = np.zeros([dataset.count(), 2 * 384 + 1])
        Y = np.empty(dataset.count())

        X.shape

        collected_keys = dataset.select(*TrainingDataset.columns).collect()

        for i, collected_key in enumerate(collected_keys):
            X[i] = np.concatenate(
                [
                    embeddings_keys[collected_key.key],
                    embeddings_keys[collected_key.previous_key],
                    np.asarray([collected_key.month]),
                ]
            )
            Y[i] = collected_key.label

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
