import logging
from typing import Optional

from python_search.configuration.configuration import PythonSearchConfiguration
from python_search.configuration.loader import ConfigurationLoader
from python_search.core_entities import Key
from python_search.entry_capture.register_new import RegisterNew
from python_search.entry_runner import EntryRunner
from python_search.error.exception import notify_exception
from python_search.events.run_performed.entity import EntryExecuted
from python_search.events.run_performed.writer import LogRunPerformedClient
from python_search.host_system.window_hide import HideWindow
from python_search.search.entries_loader import EntriesLoader
from python_search.search.search_ui.kitty_for_search_ui import KittyForSearchUI
from python_search.search.search_ui.semantic_search import SemanticSearch


class PythonSearchCli:
    """
    Welcome to PythonSearch, An open-source assistant that helps you collect, retrieve and refactor information (and programs) efficiently using Python
    """

    # all commands that are not self-explanatory should not be part of the main api, thus are marked as private.

    configuration: PythonSearchConfiguration

    @staticmethod
    def install_missing_dependencies():
        """
        Install all missing dependencies that cannot be provided through the default installer

        """
        from python_search.init.install_dependencies import InstallDependencies

        InstallDependencies().install_all()

    @staticmethod
    def new_project():
        """
        Create a new project in the current directory with the given name
        """
        from python_search.init.project import Project

        Project().new_project()

    @staticmethod
    def set_project_location(location: str):
        """
        If you have a python search project already you can specify its location with this command
        """
        from python_search.init.project import Project

        Project().set_current_project(location)

    def __init__(self, configuration: Optional[PythonSearchConfiguration] = None):
        if not configuration:
            logging.debug("No _configuration provided, using default")
        
        self.configuration = configuration
        import python_search.events

        self.events = python_search.events
        self._semantic_search = SemanticSearch
        self._entries_loader = EntriesLoader
        self._kitty_search = KittyForSearchUI

    def run_key(self, key: str):
        EntryRunner(self._get_configuration()).run(key)

    def _get_configuration(self):
        if not self.configuration:
            self.configuration = ConfigurationLoader().load_config()
        return self.configuration

    def search(self):
        """
        Opens the Search UI. Main entrypoint of the application
        """

        KittyForSearchUI.focus_or_open(self.configuration)

    def register_new_ui(self):
        """
        Starts the UI for collecting a new entry into python search
        """
        return RegisterNew().launch_ui()


    def _copy_entry_content(self, entry_str: str):
        """
        Copies the content of the provided key to the clipboard.
        Used by fzf to provide Ctrl-c functionality.
        """
        from python_search.interpreter.interpreter_matcher import InterpreterMatcher

        key = str(Key.from_fzf(entry_str))

        InterpreterMatcher.build_instance(self.configuration).clipboard(key)
        LogRunPerformedClient().send(
            EntryExecuted(key=key, query_input="", shortcut=False)
        )

    def _copy_key_only(self, entry_str: str):
        """
        Copies to clipboard the key
        """
        from python_search.apps.clipboard import Clipboard

        key = str(Key.from_fzf(entry_str))
        Clipboard().set_content(key, enable_notifications=True)
        LogRunPerformedClient().send(
            EntryExecuted(key=key, query_input="", shortcut=False)
        )

    def configure_shortcuts(self):
        """
        Generate shortcuts for the current configuration
        """
        from python_search.shortcut.generator import ShortcutGenerator

        return ShortcutGenerator(self.configuration).configure

    def _utils(self):
        """Here commands that are small topics and dont fit the rest"""

        class Utils:
            def __init__(self, configuration):
                self.configuration = configuration

            def hide_launcher(self):
                HideWindow().hide(self.configuration.APPLICATION_TITLE)

        return Utils(self.configuration)

    def _entry_type_classifier(self):
        from python_search.entry_type.classifier_inference import (
            ClassifierInferenceClient,
        )

        class EntryTypeClassifierAPI:
            def __init__(self):
                self.inference_client = ClassifierInferenceClient

        return EntryTypeClassifierAPI

    def edit_entries_main(self):
        """Edit the entries_main script"""

        from python_search.entry_capture.entries_editor import EntriesEditor

        return EntriesEditor(self.configuration).edit_default()

    @notify_exception()
    def _simulate_error(self):
        raise Exception("This is a test error")


def main():
    import fire

    fire.Fire(PythonSearchCli)


if __name__ == "__main__":
    main()
