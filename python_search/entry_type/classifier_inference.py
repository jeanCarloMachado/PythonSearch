from python_search.entry_type.entity import EntryType
from python_search.ranking.models import PythonSearchMLFlow
from python_search.ranking.next_item_predictor.features.entry_embeddings.entry_embeddings import \
    create_embeddings_from_strings


def predict_entry_type(entry_content) -> EntryType:
    model = PythonSearchMLFlow().get_entry_type_classifier(run_id='89a6693c06244e54a3c921c86bd8b15b')
    data = create_embeddings_from_strings([entry_content])

    result = model.predict(data)
    max_val = max(result[0])

    for k, v in enumerate(result[0]):
        if max_val == v:
            return EntryType.from_categorical(k)


if __name__ == '__main__':
    import fire
    fire.Fire()

