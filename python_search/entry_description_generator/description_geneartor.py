import numpy as np
from pydantic import BaseModel


max_chars_from_key = 30
max_chars_of_body = 100
maxlen = max_chars_of_body + max_chars_from_key


class EntryKeyGeneratorCmd(BaseModel):
    content: str
    temperature: float = 0.2


class DescriptionGenerator:

    RUN_ID = "054613ec285f4b1c86ee81de98b08d06"

    def __init__(self):
        try:
            from python_search.search.models import PythonSearchMLFlow

            self._model = PythonSearchMLFlow().get_entry_description_geneartor(
                run_id=DescriptionGenerator.RUN_ID
            )

            self._chars = PythonSearchMLFlow().get_entry_description_geneartor_dict(
                run_id=DescriptionGenerator.RUN_ID
            )
            self._char_indices = dict(
                (char, self._chars.index(char)) for char in self._chars
            )
        except Exception as e:
            print("Could not load descritpion generator {}".format(e))
            return

    def generate(self, cmd: EntryKeyGeneratorCmd):

        result = ""
        for i in range(0, max_chars_from_key):
            text = cmd.content
            encoded = self._transform(text)
            preds = self._model.predict(encoded)

            next_index = self.sample(preds[0], cmd.temperature)
            next_char = self._chars[next_index]
            text = text + next_char
            result += next_char
        return result

    def sample(self, preds, temperature=1.0):
        preds = np.asanyarray(preds).astype("float64")
        preds = np.log(preds) / temperature

        exp_preds = np.exp(preds)
        preds = exp_preds / np.sum(exp_preds)
        probas = np.random.multinomial(1, preds, 1)
        return np.argmax(probas)

    def _transform(self, text):

        text_len = len(text)
        missing_spaces = text_len < (maxlen - 3)

        if missing_spaces:
            text = " " * missing_spaces

        text = text + " = "

        encoded = np.zeros((1, maxlen, len(self._chars)))

        for i, char in enumerate(text):
            encoded[0, i, self._char_indices[char]] = 1

        return encoded


if __name__ == "__main__":
    import fire

    fire.Fire(DescriptionGenerator)
