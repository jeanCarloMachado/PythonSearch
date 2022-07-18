"""
Clients should depend on a configuration instance (config) rather than in the class,
the class should only be used for type annotation.
This way we can have multiple configs depending of the enviroment.
"""
import os
from typing import List, Optional

from python_search.entries_group import EntriesGroup
from python_search.environment import is_mac
from python_search.features import FeaturesSupport


class SearchRunConfiguration:
    NLP_PICKLED_EMBEDDINGS: str = f"{os.getenv('HOME')}/.python_search_nlp_embeddings"
    # editor used to edit the entries
    EDITOR = "vim"


class DataConfig:
    """
    Configuration with locations of data, models and names of files.
    """

    # output of the model
    base_data_folder = "/data/python_search"
    prediction_batch_location = base_data_folder + "/predict_input_lenght/latest"
    # a copy of the search run entries for the feature store
    entries_dump = base_data_folder + "/entries_dumped/latest"
    entries_dump_file = base_data_folder + "/entries_dumped/latest/000.parquet"
    cached_configuration = "/tmp/search_and_run_configuration_cached"
    MLFLOW_MODELS_PATH = f"{os.environ['HOME']}/projects/PySearchEntries/mlflow"
    BASELINE_EXPERIMENT_NAME = f"baseline_rank_v0"
    NEXT_ITEM_EXPERIMENT_NAME = f"next_item_v0"
    DATA_WAREHOUSE_FOLDER = base_data_folder + "/data_warehouse"
    SEARCH_RUNS_PERFORMED_FOLDER = (
        base_data_folder + "/data_warehouse/dataframes/SearchRunPerformed"
    )


# @todo do not depend on this config directly rather depend on the base configuration
config = SearchRunConfiguration()


class KafkaConfig:
    default_port: str = "9092"
    host: str = f"localhost:{default_port}"


class RedisConfig:
    host = "localhost"
    port = 6379 if is_mac() else 6378


class PythonSearchConfiguration(EntriesGroup):
    """
    The main configuration of Python Search
    Everything to customize about the application should be tunneled through this clas
    """

    APPLICATION_TITLE = "SearchPythonSearch"
    commands: dict
    simple_gui_theme = "SystemDefault1"
    simple_gui_font_size = 12

    def __init__(
        self,
        *,
        entries: Optional[dict] = None,
        entries_groups: Optional[List[EntriesGroup]] = None,
        supported_features: Optional[FeaturesSupport] = None,
    ):
        if entries:
            self.commands = entries

        if entries_groups:
            self.aggregate_commands(entries_groups)

        if supported_features:
            self.supported_features = supported_features
        else:
            self.supported_features = FeaturesSupport.default()


class ConfigurationLoader:
    """
    Loads the application from the environment.py
    """

    def load_entries(self):

        env_name = "PYTHON_SEARCH_ENTRIES_FOLDER"

        if env_name not in os.environ:
            raise Exception(f"{env_name} must be set to load the entries dynamically")

        print(f"Env: {env_name}={os.environ[env_name]}")
        folder = os.environ[env_name]

        entries_location = os.path.join(folder, "entries/main.py")

        if not os.path.exists(entries_location):
            raise Exception(f"Could not find entries main file {entries_location}")

        import sys

        sys.path.append(folder)
        import entries.main as entries_main

        config = entries_main.entries

        return config

    def load_config(self) -> PythonSearchConfiguration:

        env_name = "PYTHON_SEARCH_CONFIG_FOLDER"

        if env_name not in os.environ:
            raise Exception(f"{env_name} must be set to load the config dynamically")

        print(f"Env: {env_name}={os.environ[env_name]}")
        folder = os.environ[env_name]

        config_location = os.path.join(folder, "entries/main.py")

        if not os.path.exists(config_location):
            raise Exception(f"Could not find config file {config_location}")

        import sys

        sys.path.append(folder)
        from entries.main import config

        return config

    def reload(self):
        import importlib

        import entries.main as entries_main

        importlib.reload(entries_main)
        config = entries_main.config

        return config
