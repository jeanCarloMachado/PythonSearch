"""
Clients should depend on a configuration instance (config) rather than in the class,
the class should only be used for type annotation.
This way we can have multiple configs depending of the enviroment.
"""
import os


class SearchRunConfiguration:
    NLP_PICKLED_EMBEDDINGS: str = f"{os.getenv('HOME')}/.python_search_nlp_embeddings"


class DataPaths:
    # output of the model
    prediction_batch_location = "/data/python_search/predict_input_lenght/latest"
    # a copy of the search run entries for the feature store
    entries_dump = "/data/python_search/entries_dumped/latest"
    entries_dump_file = "/data/python_search/entries_dumped/latest/000.parquet"
    commands_performed = "/data/grimoire/message_topics/run_key_command_performed"
    cached_configuration = "/tmp/search_and_run_configuration_cached"


config = SearchRunConfiguration()
