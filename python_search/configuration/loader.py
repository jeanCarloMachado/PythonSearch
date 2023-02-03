import logging
import os

from python_search.configuration.configuration import PythonSearchConfiguration


class ConfigurationLoader:
    """
    Loads the application from the environment.py
    """

    _instance = None

    def get_config_instance(self):
        if not ConfigurationLoader._instance:
            ConfigurationLoader._instance = self.load_config()
        return ConfigurationLoader._instance

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
