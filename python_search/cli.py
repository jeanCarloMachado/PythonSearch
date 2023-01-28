import logging
from typing import Optional

from python_search.apps.window_manager import WindowManager
from python_search.configuration.configuration import PythonSearchConfiguration
from python_search.configuration.loader import ConfigurationLoader
from python_search.core_entities import Key
from python_search.entry_runner import EntryRunner
from python_search.environment import is_mac
from python_search.events.run_performed import RunPerformed
from python_search.events.run_performed.writer import LogRunPerformedClient
from python_search.search_ui.kitty import FzfInKitty
from python_search.search_ui.fzf import Fzf
from python_search.search_ui.preview import Preview

class PythonSearchCli:
    """
    The command line application, entry point of the program.

    Try to avoid adding direct commands, prefer instead to add objects as parts of functions
    """

    # all commands that are not self-explanatory should not be part of the main api, thus are marked as private.

    configuration: PythonSearchConfiguration

    @staticmethod
    def install_missing_dependencies():
        """
        Install all missing dependencies that cannot be provided thorugh the default installer

        For mac: brew related dependenceis

        """
        from python_search.init.install_dependencies import InstallDependencies

        InstallDependencies().install_all()

    @staticmethod
    def new_project(project_name: str):
        """Create a new project in the current directory with the given name"""
        from python_search.init.project import Project

        Project().new_project(project_name)

    @staticmethod
    def set_project_location(location: str):
        """For existing"""
        from python_search.init.project import Project

        Project().set_current_project(location)

    def __init__(self, configuration: Optional[PythonSearchConfiguration] = None):
        """
        Keep this constructor small and import dependencies inside the functions
        so they keep being fast
        """
        if not configuration:
            logging.debug("No _configuration provided, using default")
            try:
                configuration = ConfigurationLoader().load_config()
            except Exception as e:
                print(f"Did not find any config to load, error: {e}")

                # early return so we dont set the remaining attributes
                return

        self.configuration = configuration
        self.run_key = EntryRunner(self.configuration).run

    def search(self, only_fzf=False):
        """
        Opens the Search UI. Main entrypoint of the application
        """
        if only_fzf:
            return Fzf(self.configuration).run()

        FzfInKitty(self.configuration).run()


    def register_new_ui(self):
        """
        Starts the UI for collecting a new entry into pythonsearch
        """
        from python_search.entry_capture.register_new import RegisterNew

        return RegisterNew(self.configuration).launch_ui

    def _copy_entry_content(self, entry_str: str):
        """
        Copies the content of the provided key to the clipboard.
        Used by fzf to provide Ctrl-c functionality.
        """
        from python_search.interpreter.interpreter_matcher import InterpreterMatcher

        key = str(Key.from_fzf(entry_str))

        InterpreterMatcher.build_instance(self.configuration).clipboard(key)
        LogRunPerformedClient().send(
            RunPerformed(key=key, query_input="", shortcut=False)
        )

    def _copy_key_only(self, entry_str: str):
        """
        Copies to clipboard the key
        """
        from python_search.apps.clipboard import Clipboard

        key = str(Key.from_fzf(entry_str))
        Clipboard().set_content(key, enable_notifications=True)
        LogRunPerformedClient().send(
            RunPerformed(key=key, query_input="", shortcut=False)
        )

    def configure_shortcuts(self):
        """
        Generate shorcuts for the appliable environments
        """
        from python_search.shortcut.generator import ShortcutGenerator

        return ShortcutGenerator(self.configuration).configure


    def _ranking(self):
        from python_search.search.search import Search

        return Search(self.configuration)

    def _features(self):
        """Feature toggle system"""
        from python_search.feature_toggle import FeatureToggle

        return FeatureToggle()

    def _utils(self):
        """Here commands that are small topics and dont fit the rest"""

        class Utils:
            def __init__(self, configuration):
                self.configuration = configuration

            def hide_launcher(self):
                """hide the search launcher -i2 specific"""
                if is_mac():
                    import os

                    os.system(
                        """osascript -e 'tell application "System Events" to keystroke "H" using {command down}'"""
                    )
                WindowManager.load_from_environment().hide_window(
                    self.configuration.APPLICATION_TITLE
                )

        return Utils(self.configuration)

    def _preview_entry(self, entry_text: str):
        """
        Recives entries from fzf and show them formatted for the preview window
        """
        Preview().display(entry_text)

    def _entry_type_classifier(self):

        from python_search.entry_type.classifier_inference import (
            ClassifierInferenceClient,
        )

        class EntryTypeClassifierAPI:
            def __init__(self):
                self.inference_client = ClassifierInferenceClient

        return EntryTypeClassifierAPI


def _error_handler(e):
    import sys
    import traceback

    exc_info = sys.exc_info()
    logging.warning(
        f"Unhandled exception: {e}".join(traceback.format_exception(*exc_info))
    )

    raise e


def main():
    import fire

    fire.Fire(PythonSearchCli)
