import os
from typing import Any, Tuple

import mlflow
import numpy as np
from keras import layers
from keras.models import Sequential

Model = Any


class TrainKeras:

    EPOCHS = 30
    TEST_SPLIT_SIZE = 0.10
    BATCH_SIZE = 128

    def __init__(self, epochs=None):
        if not epochs:
            epochs = TrainKeras.EPOCHS
        self.epochs = epochs
        # enable the profiling scaffolding
        os.environ["TIME_IT"] = "1"

    def train(self, X_train, X_test, Y_train, Y_test) -> Model:

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

        model.fit(
            X_train,
            Y_train,
            epochs=self.epochs,
            batch_size=TrainKeras.BATCH_SIZE,
            validation_data=(X_test, Y_test),
        )
        # self._plot_training_history(history)

        return model

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
