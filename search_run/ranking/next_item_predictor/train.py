from typing import Dict, List

import mlflow
import numpy as np
import pyspark.sql.functions as F

from search_run.config import DataConfig
from search_run.ranking.entry_embeddings import create_indexed_embeddings
from search_run.ranking.models import PythonSearchMLFlow
from search_run.ranking.next_item_predictor.training_dataset import TrainingDataset


class Train:
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

        return model

    def train(self, dataset, plot_history=False):

        X, Y = self.create_XY(dataset)

        from sklearn.model_selection import train_test_split

        X_train, X_test, Y_train, Y_test = train_test_split(
            X, Y, test_size=0.20, random_state=42
        )

        from keras import layers
        from keras.models import Sequential

        # 20 epochs looks like the ideal in the current architectur
        epochs = 20
        print("Epochs:", epochs)
        model = Sequential()
        model.add(layers.Dense(32, activation="relu", input_shape=X[1].shape))
        model.add(layers.Dense(1))
        model.compile(optimizer="rmsprop", loss="mse", metrics=["mae"])

        history = model.fit(
            X_train,
            Y_train,
            epochs=epochs,
            batch_size=32,
            validation_data=(X_test, Y_test),
        )

        if plot_history:
            import matplotlib.pyplot as plt

            loss = history.history["loss"]
            val_loss = history.history["val_loss"]

            epochs_range = range(1, epochs + 1)
            plt.plot(epochs_range, loss, "bo", label="Training Loss")
            plt.plot(epochs_range, val_loss, "b", label="Validation Loss")
            plt.title("Training and validation loss")
            plt.xlabel("Epochs")
            plt.ylabel("Loss")
            plt.legend()
            plt.show()
            return

        train_mse, train_mae = model.evaluate(X_train, Y_train)
        test_mse, test_mae = model.evaluate(X_test, Y_test)

        metrics = {
            "train_mse": train_mse,
            "train_mae": train_mae,
            "test_mse": test_mse,
            "test_mae": test_mae,
        }
        print(metrics)
        return model, metrics

    def create_XY(self, dataset):
        """
        Transform the dataset into X and Y
        """

        embeddings_keys = self.create_embeddings_historical_keys(dataset)

        # + 1 is for the week number
        X = np.zeros([dataset.count(), 2 * 384 + 1])
        Y = np.empty(dataset.count())

        X.shape

        collected_keys = dataset.select(*TrainingDataset.columns).collect()

        for i, collected_key in enumerate(collected_keys):
            X[i] = np.concatenate(
                [
                    embeddings_keys[collected_key.key],
                    embeddings_keys[collected_key.previous_key],
                    np.asarray([collected_key.week]),
                ]
            )
            Y[i] = collected_key.label

        return X, Y

    def create_embeddings_historical_keys(self, dataset) -> Dict[str, np.ndarray]:
        """create embeddings for all historical keys"""

        # add embeddings to the dataset
        all_keys = self._get_all_keys_dataset(dataset)

        return create_indexed_embeddings(all_keys)

    def _get_all_keys_dataset(self, dataset) -> List[str]:
        collected_keys = dataset.select("key", "previous_key").collect()

        keys = []
        for collected_keys in collected_keys:
            keys.append(collected_keys.key)
            keys.append(collected_keys.previous_key)

        return keys

    def baseline_mse(self, dataset):
        # naive approach of setting the same as input and output, used as baseline to measure the real model against
        from sklearn.metrics import mean_squared_error

        # apply only to the  ones with the same name in input and output
        # complete dataset 8k, with the same name in input and output 150
        naive = (
            dataset.filter("key == previous_key")
            .select("key", "label")
            .withColumn("baseline", F.lit(1))
        )
        pd_naive = naive.select("label", "baseline").toPandas()
        return mean_squared_error(pd_naive.label, pd_naive.baseline)
