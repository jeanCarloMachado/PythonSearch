from typing import List, Tuple
import random
import sys
import numpy as np
from python_search.config import ConfigurationLoader
from keras import layers
import keras
from python_search.search.next_item_predictor.mlflow_logger import configure_mlflow


def extract_string_from_entries(entries) -> List[str]:
    X = []
    for key, entry in entries.items():
        if "url" in entry:
            item = str(entry["url"])
        if "snippet" in entry:
            item = str(entry["snippet"])
        if "file" in entry:
            item = str(entry["file"])
        if "callable" in entry:
            item = str(entry["callable"])
        if "cmd" in entry:
            item = str(entry["cmd"])
        if "cli_cmd" in entry:
            item = str(entry["cli_cmd"])

        X.append(item)

    return X


def sample(preds, temperature=1.0):
    preds = np.asanyarray(preds).astype("float64")
    preds = np.log(preds) / temperature

    exp_preds = np.exp(preds)
    preds = exp_preds / np.sum(exp_preds)
    probas = np.random.multinomial(1, preds, 1)
    return np.argmax(probas)


def run(epochs=50):
    # create dataset
    entries = ConfigurationLoader().load_entries()
    result = extract_string_from_entries(entries)
    dataset = list(zip(result, entries.keys()))

    filtered_dataset: List[Tuple[str, str]] = []
    for value, key in dataset:
        if key.startswith("no key"):
            continue
        filtered_dataset.append([value, key])

    sentences = []
    next_char = []
    max_chars_from_key = 30
    max_chars_of_body = 100
    maxlen = max_chars_of_body + max_chars_from_key

    for value, key in filtered_dataset:
        for i in range(0, len(key)):
            if i > (max_chars_from_key - 3):
                break

            sentence = value[0:100] + " = " + key[0:(i)]

            current_size = len(sentence)
            if current_size < maxlen:
                sentence = (" " * (maxlen - current_size)) + sentence

            sentences.append(sentence)
            next_char.append(key[i])

    for i, sentence in enumerate(sentences[0:100]):
        print(f"sentence: {sentence}, next_char = {next_char[i]} ")

    text = " ".join(next_char) + " ".join(sentences)

    chars = sorted(list(set(text)))
    char_indices = dict((char, chars.index(char)) for char in chars)

    chars[0:5]

    x = np.zeros((len(sentences), maxlen, len(chars)), dtype=np.bool)
    y = np.zeros((len(sentences), len(chars)), dtype=np.bool)

    for i, sentence in enumerate(sentences):
        # print(f"Sentence: {sentence}")
        for t, char in enumerate(sentence):
            # print(t)

            x[i, t, char_indices[char]] = 1

        y[i, char_indices[next_char[i]]] = 1

    model = keras.models.Sequential()
    model.add(layers.LSTM(128, input_shape=(maxlen, len(chars))))
    model.add(layers.Dense(len(chars), activation="softmax"))
    optimizer = keras.optimizers.RMSprop(lr=0.011)
    model.compile(loss="categorical_crossentropy", optimizer=optimizer)

    # train model
    epoch = 0
    for epoch in range(1, epochs):
        print("\n => Epoch: ", epoch)
        model.fit(x, y, batch_size=64, epochs=1)
        start_index = random.randint(0, len(text) - maxlen - 1)
        generated_text = text[start_index : start_index + maxlen]
        print(' -- generating with seed: "' + generated_text + '"')

        for temperature in [0.2, 1.2]:
            print(f"\n ----  Temperature: {temperature}, Input text follows: ")
            sys.stdout.write(generated_text)
            print("\n Generated text follows: ")
            for i in range(30):
                sampled = np.zeros((1, maxlen, len(chars)))
                for t, char in enumerate(generated_text):
                    sampled[0, t, char_indices[char]] = 1

                preds = model.predict(sampled, verbose=0)[0]
                next_index = sample(preds, temperature)
                next_char = chars[next_index]

                generated_text += next_char
                generated_text = generated_text[1:]

                sys.stdout.write(next_char)

    mlflow = configure_mlflow(experiment_name="entry_description_generator")
    mlflow.start_run()
    mlflow.log_dict(chars, "chars")
    mlflow.log_param("epochs", epoch)
    mlflow.keras.log_model(model, "model")
    mlflow.end_run()


if __name__ == "__main__":
    import fire

    fire.Fire()
