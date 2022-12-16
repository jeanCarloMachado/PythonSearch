import uuid


from python_search.entry_type.classifier_inference import get_value_and_label
from python_search.entry_type.entity import EntryType
from python_search.config import ConfigurationLoader, DataConfig
import pandas as pd
import matplotlib.pyplot as plt

from python_search.infrastructure.arize import Arize
from python_search.search.next_item_predictor.mlflow_logger import configure_mlflow
from python_search.search.next_item_predictor.features.entry_embeddings.entry_embeddings import (
    create_embeddings_from_strings,
)
import os
import numpy as np
from keras import models
from keras import layers
from keras.utils.np_utils import to_categorical


class Pipeline:

    INPUT_DIMENSIONS = 384 + 2

    def __init__(self):
        self._arize_client = Arize().get_client()

    def run(self, embeddings_cache=None, cache=False, disable_arize=False):
        df = self.create_dataset()
        input_list = df["input"].tolist()
        number_of_items = len(input_list)
        embeddings = None

        # cache flag can enable caching of embeddings if not set specifically
        embeddings_cache = embeddings_cache if embeddings_cache else cache

        CACHE_LOCATION = "/root/.cache/entry_type_np_cache.npy"
        if embeddings_cache and os.path.exists(CACHE_LOCATION):
            print("Using transformed data from cache")
            embeddings = np.load(CACHE_LOCATION, allow_pickle=True)
            if len(embeddings) != number_of_items:
                print("Cache size does not match dataset size")
                embeddings = None

        if embeddings is None:
            embeddings = create_embeddings_from_strings(input_list)
            np.save(CACHE_LOCATION, embeddings)

        X = np.zeros([number_of_items, Pipeline.INPUT_DIMENSIONS])
        for i in range(0, number_of_items):
            X[i] = np.concatenate(
                (
                    embeddings[i],
                    np.asarray([1 if df["has_pipe"].iloc[i] else 0]),
                    np.asarray([1 if df["has_double_minus"].iloc[i] else 0]),
                )
            )

        categorical_labels = to_categorical(df["label"].tolist())

        mlflow = configure_mlflow(
            experiment_name=DataConfig.ENTRY_TYPE_CLASSIFIER_EXPERIMENT_NAME
        )
        mlflow.keras.autolog()
        with mlflow.start_run() as modelInfo:
            model = models.Sequential()
            run_id = mlflow.active_run().info.run_id
            model.add(
                layers.Dense(
                    128, activation="relu", input_shape=(Pipeline.INPUT_DIMENSIONS,)
                )
            )
            model.add(layers.Dense(64, activation="relu"))
            model.add(layers.Dense(5, activation="softmax"))

            model.compile(
                optimizer="rmsprop",
                loss="categorical_crossentropy",
                metrics=["accuracy"],
            )

            x_train = X[1000:]
            y_train = categorical_labels[1000:]

            # separate 1000 for validation
            x_val = X[:1000]
            y_val = categorical_labels[:1000]

            history = model.fit(
                x_train,
                y_train,
                epochs=20,
                batch_size=512,
                validation_data=(x_val, y_val),
            )
            mlflow.keras.log_model(model, "model", keras_module="keras")
            run_id = mlflow.active_run().info.run_id
            print("run id: ", run_id)

        if not disable_arize and Arize.is_installed():
            from arize.utils.types import ModelTypes, Environments, Embedding

            print("Sending validation values to arize")
            for key, entry in enumerate(x_val):
                value, label = get_value_and_label(
                    model.predict(np.asarray([entry]))[0]
                )
                result = self._arize_client.log(
                    model_id=Arize.MODEL_ID,
                    model_version=Arize.MODEL_VERSION,
                    model_type=ModelTypes.SCORE_CATEGORICAL,
                    batch_id=run_id,
                    prediction_id=str(uuid.uuid4()),
                    features={"has_pipe": entry[384], "has_double_minus": entry[385]},
                    embedding_features={
                        "content": Embedding(vector=entry, data=input_list[key])
                    },
                    prediction_label=(label, float(value)),
                    actual_label=(
                        get_value_and_label(y_val[key])[1],
                        float(get_value_and_label(y_val[key])[0]),
                    ),
                    environment=Environments.VALIDATION,
                )
                Arize.arize_responses_helper(result)

        loss = history.history["loss"]
        val_loss = history.history["val_loss"]

        epochs = range(1, len(loss) + 1)
        plt.plot(epochs, loss, "bo", label="TrainingLoss")
        plt.plot(epochs, val_loss, "b", label="ValidationLoss")
        plt.legend()
        plt.show()

        accuracy = history.history["accuracy"]
        val_acc = history.history["val_accuracy"]

        epochs = range(1, len(loss) + 1)
        plt.plot(epochs, accuracy, "bo", label="TrainingAccuracy")
        plt.plot(epochs, val_acc, "b", label="ValidationAccuracy")
        plt.legend()
        plt.show()

    def create_dataset(self) -> pd.DataFrame:
        entries = ConfigurationLoader().load_entries()
        entries
        dataset = []

        for key, entry in entries.items():
            X = key + " "
            y = None
            if "url" in entry:
                y = EntryType.to_categorical(EntryType.URL)
                X = X + str(entry["url"])
            if "snippet" in entry:
                y = EntryType.to_categorical(EntryType.SNIPPET)
                X = X + str(entry["snippet"])
            if "file" in entry:
                y = EntryType.to_categorical(EntryType.FILE)
                X = X + str(entry["file"])
            if "callable" in entry:
                y = EntryType.to_categorical(EntryType.CALLABLE)
                X = X + str(entry["callable"])
            if "cmd" in entry:
                y = EntryType.to_categorical(EntryType.CMD)
                X = X + str(entry["cmd"])
            if "cli_cmd" in entry:
                y = EntryType.to_categorical(EntryType.CMD)
                X = X + str(entry["cli_cmd"])

            if y is None:
                raise Exception(f"Could not map key '{key}' to any value {entry}")

            has_pipe = "|" in X
            has_double_minus = "--" in X

            dataset.append([X, has_pipe, has_double_minus, y])

        df = pd.DataFrame(
            dataset, columns=["input", "has_pipe", "has_double_minus", "label"]
        )
        return df


if __name__ == "__main__":
    import fire

    fire.Fire()
