from __future__ import annotations
import json
import uuid
from typing import Optional

from arize.utils.types import ModelTypes, Environments
from pydantic import BaseModel

from python_search.entry_type.entity import EntryType
from python_search.infrastructure.arize import Arize


class EntryData(BaseModel):
    content: str
    key: Optional[str]

class PredictEntryTypeInference():
    def __init__(self):
        # Instantiate an Arize Client object using your API and Space keys
        self._arize_client = Arize().get_client()

    def predict_entry_type_from_dict(self, entry: dict) -> EntryType:
        return self.predict_entry_type(EntryData(**entry))

    def predict_entry_type(self, entry_data: EntryData) -> EntryType:

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
                result = EntryType.from_categorical(k)
                break

        self._arize_client.log(
            model_id="entry_type_classifier",
            model_type=ModelTypes.SCORE_CATEGORICAL,
            model_version="v1",
            prediction_id=str(uuid.uuid4()),
            features=entry_data.dict(),
            prediction_label=result.value,
            environment=Environments.PRODUCTION,
        )


        return result

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
