"""
Clients should depend on a configuration instance (config) rather than in the class,
the class should only be used for type annotation.
This way we can have multiple configs depending of the enviroment.
"""
import logging
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
    host: str = f"127.0.0.1:{default_port}"


class RedisConfig:
    host = "localhost"
    port = 6379 if is_mac() else 6378


class PythonSearchConfiguration(EntriesGroup):
    """
    The main configuration of Python Search
    Everything to customize about the application is configurable via code through this class
    """

    APPLICATION_TITLE = "SearchPythonSearch"
    commands: dict
    simple_gui_theme = "SystemDefault1"
    simple_gui_font_size = 14

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
            self.supported_features: FeaturesSupport = supported_features
        else:
            self.supported_features: FeaturesSupport = FeaturesSupport.default()


class ConfigurationLoader:
    """
    Loads the application from the environment.py
    """

    def load_config(self) -> PythonSearchConfiguration:

        folder = self.get_project_root()
        config_location = f"{folder}/entries_main.py"

        if not os.path.exists(config_location):
            raise Exception(f"Could not find config file {config_location}")

        import sys

        sys.path.insert(0, folder)
        from entries_main import config

        return config

    def get_project_root(self):
        env_name = "PS_ENTRIES_HOME"
        current_project_location = (
            os.environ["HOME"] + "/.config/python_search/current_project"
        )

        folder = None

        if env_name in os.environ:
            logging.debug(
                f"Env exists and takes precedence: {env_name}={os.environ[env_name]}"
            )
            folder = os.environ[env_name]

        if os.path.isfile(current_project_location):
            with open(current_project_location) as f:
                folder = f.readlines()[0].strip()

        if not folder:
            raise Exception(
                f"Either {current_project_location} or {env_name} must be set to find entries"
            )
        return folder

    def load_entries(self):
        config = self.load_config()
        return config.commands

    def reload(self):
        import importlib

        import entries_main

        importlib.reload(entries_main)
        config = entries_main.config

        return config
