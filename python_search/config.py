"""
Clients should depend on a configuration instance (config) rather than in the class,
the class should only be used for type annotation.
This way we can have multiple configs depending of the enviroment.
"""
import datetime
import logging
import os
from typing import List, Optional, Tuple

from python_search.entries_group import EntriesGroup
from python_search.environment import is_mac
from python_search.features import PythonSearchFeaturesSupport




class DataConfig:
    """
    Configuration with locations of _entries, models and names of files.
    """

    # output of the _model
    base_data_folder = f"{os.environ['HOME']}/.data/data/python_search"
    BASE_DATA_COLLECTOR_FOLDER = f"{os.environ['HOME']}/.data/data_collection"
    prediction_batch_location = base_data_folder + "/predict_input_lenght/latest"
    # a copy of the search run _entries for the feature store
    entries_dump = base_data_folder + "/entries_dumped/latest"
    entries_dump_file = base_data_folder + "/entries_dumped/latest/000.parquet"
    cached_configuration = "/tmp/search_and_run_configuration_cached"
    MLFLOW_MODELS_PATH = f"/entries/mlflow"
    BASELINE_EXPERIMENT_NAME = f"baseline_rank_v0"
    NEXT_ITEM_EXPERIMENT_NAME = f"next_item_v1"
    ENTRY_TYPE_CLASSIFIER_EXPERIMENT_NAME = f"entry_type_classifier_v2"
    DATA_WAREHOUSE_FOLDER = base_data_folder + "/data_warehouse"
    CLEAN_EVENTS_FOLDER = DATA_WAREHOUSE_FOLDER + "/clean"
    SEARCH_RUNS_PERFORMED_FOLDER = (
        base_data_folder + "/data_warehouse/dataframes/SearchRunPerformed"
    )


# @todo do not depend on this config directly rather depend on the base configuration

class KafkaConfig:
    default_port: str = "9092"
    host: str = f"127.0.0.1:{default_port}"


class RedisConfig:
    host = "127.0.0.1" if is_mac() else "host.docker.internal"
    port = 6379


class PythonSearchConfiguration(EntriesGroup):
    """
    The main _configuration of Python Search
    Everything to customize about the application is configurable via code through this class
    """

    APPLICATION_TITLE = "PythonSearchWindow"
    commands: dict
    simple_gui_theme = "SystemDefault1"
    simple_gui_font_size = 14
    _default_tags = None
    tags_dependent_inserter_marks = None
    _initialization_time = None
    _default_text_editor = "vim"

    def __init__(
        self,
        *,
        entries: Optional[dict] = None,
        entries_groups: Optional[List[EntriesGroup]] = None,
        supported_features: Optional[PythonSearchFeaturesSupport] = None,
        default_tags=None,
        tags_dependent_inserter_marks: Optional[dict[str, Tuple[str, str]]] = None,
        default_text_editor: Optional[str] = None,
    ):
        """

        :param entries:
        :param entries_groups:
        :param supported_features:
        :param default_tags:
        :param tags_dependent_inserter_marks:
        :param default_text_editor:
        """
        if entries:
            self.commands = entries

        if entries_groups:
            self.aggregate_commands(entries_groups)

        if supported_features:
            self.supported_features: PythonSearchFeaturesSupport = supported_features
        else:
            self.supported_features: PythonSearchFeaturesSupport = (
                PythonSearchFeaturesSupport.default()
            )

        if default_tags:
            self._default_tags = default_tags

        self.tags_dependent_inserter_marks = tags_dependent_inserter_marks


        self._initialization_time = datetime.datetime.now()
        self._default_text_editor = default_text_editor


    def get_text_editor(self):
        return self._default_text_editor

    def get_default_tags(self):
        return self._default_tags


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

        if folder not in sys.path:
            sys.path.insert(0, folder)
        import copy
        from entries_main import config

        return copy.deepcopy(config)

    def reload(self):
        """
        reload _entries for when we change it
        """
        import importlib

        import entries_main

        importlib.reload(entries_main)

        import copy

        import entries_main

        return copy.deepcopy(entries_main.config)

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
                f"Either {current_project_location} or {env_name} must be set to find _entries"
            )
        return folder

    def load_entries(self):
        return self.load_config().commands
