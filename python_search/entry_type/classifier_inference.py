import json
from typing import Optional

from pydantic import BaseModel

from python_search.entry_type.entity import EntryType


class EntryData(BaseModel):
    content: str
    key: Optional[str]


def predict_entry_type(entry_data: EntryData) -> EntryType:
    import contextlib

    from python_search.search.models import PythonSearchMLFlow

    model = PythonSearchMLFlow().get_entry_type_classifier(
        run_id="89a6693c06244e54a3c921c86bd8b15b"
    )
    from python_search.search.next_item_predictor.features.entry_embeddings.entry_embeddings import \
        create_embeddings_from_strings

    data = create_embeddings_from_strings([entry_data.content])

    result = model.predict(data)
    max_val = max(result[0])

    for k, v in enumerate(result[0]):
        if max_val == v:
            return EntryType.from_categorical(k)


class ClassifierInferenceClient:
    def predict_from_content(self, content: str):
        return self.predict(EntryData(content=content))

    def predict(self, data: EntryData) -> Optional[EntryType]:
        import requests

        try:
            result = requests.post(
                url="http://localhost:8000/entry_type/classify", json=data.__dict__
            )
            data = json.loads(result.text)
            return data["predicted_type"]
        except BaseException as e:
            print(f"Logging results failed, reason: {e}")
            return None


def main():
    import fire

    fire.Fire()


if __name__ == "__main__":
    main()
