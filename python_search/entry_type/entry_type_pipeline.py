from python_search.entry_type.entity import EntryType
from python_search.config import ConfigurationLoader
import pandas as pd
import matplotlib.pyplot as plt
from python_search.search.next_item_predictor.mlflow_logger import configure_mlflow
from python_search.search.next_item_predictor.features.entry_embeddings.entry_embeddings import \
    create_embeddings_from_strings
import os
import numpy as np

class Pipeline:

    def run(self, embeddings_cache=False):
        df = self.create_dataset()

        if embeddings_cache:
            if not os.path.exists("/tmp/entry_type_np_cache.npy"):
                raise Exception("Cache not found")
            print("Using transformed data from cache")
            embeddings = np.load("/tmp/entry_type_np_cache.npy", allow_pickle=True)
        else:
            embeddings = create_embeddings_from_strings(df['input'].tolist())
            np.save("/tmp/entry_type_np_cache.npy", embeddings)

        from keras.utils.np_utils import to_categorical
        categorical_labels = to_categorical(df['label'].tolist())

        from keras import models
        from keras import layers

        mlflow = configure_mlflow(experiment_name="entry_type_classifier")
        mlflow.autolog()
        with mlflow.start_run():
            model = models.Sequential()
            model.add(layers.Dense(128, activation='relu', input_shape=(384,)))
            model.add(layers.Dense(64, activation='relu'))
            model.add(layers.Dense(5, activation='softmax'))

            model.compile(optimizer='rmsprop', loss='categorical_crossentropy', metrics=['accuracy'])

            x_train = embeddings[1000:]
            y_train = categorical_labels[1000:]

            # separate 1000 for validation
            x_val = embeddings[:1000]
            y_val = categorical_labels[:1000]

            history = model.fit(x_train, y_train, epochs=20, batch_size=512, validation_data=(x_val, y_val))
            mlflow.keras.log_model(model, "model", keras_module="keras")


        loss = history.history['loss']
        val_loss = history.history['val_loss']


        epochs = range(1, len(loss) + 1)
        plt.plot(epochs, loss, 'bo', label='TrainingLoss')
        plt.plot(epochs, val_loss, 'b', label='ValidationLoss')
        plt.legend()
        plt.show()


        accuracy = history.history['accuracy']
        val_acc = history.history['val_accuracy']

        epochs = range(1, len(loss) + 1)
        plt.plot(epochs, accuracy, 'bo', label='TrainingAccuracy')
        plt.plot(epochs, val_acc, 'b', label='ValidationAccuracy')
        plt.legend()
        plt.show()

    def create_dataset(self) -> pd.DataFrame:
        entries = ConfigurationLoader().load_entries()
        entries
        dataset = []

        for key, entry in entries.items():
            X = key + " "
            y = None
            if 'url' in entry:
                y = EntryType.to_categorical(EntryType.URL)
                X = X + str(entry['url'])
            if 'snippet' in entry:
                y = EntryType.to_categorical(EntryType.SNIPPET)
                X = X + str(entry['snippet'])
            if 'file' in entry:
                y = EntryType.to_categorical(EntryType.FILE)
                X = X + str(entry['file'])
            if 'callable' in entry:
                y = EntryType.to_categorical(EntryType.CALLABLE)
                X = X + str(entry['callable'])
            if 'cmd' in entry:
                y = EntryType.to_categorical(EntryType.CMD)
                X = X + str(entry['cmd'])
            if 'cli_cmd' in entry:
                y = EntryType.to_categorical(EntryType.CMD)
                X = X + str(entry['cli_cmd'])

            if y is None:
                raise Exception(f"Could not map key '{key}' to any value {entry}")

            dataset.append([X, y])

        df = pd.DataFrame(dataset, columns=['input', 'label'])
        return df




if __name__ == '__main__':
    import fire
    fire.Fire()

