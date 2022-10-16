import logging

from python_search.apps.window_manager import WindowManager
from python_search.config import ConfigurationLoader, PythonSearchConfiguration
from python_search.entry_runner import EntryRunner
from python_search.environment import is_mac
from python_search.events.run_performed import RunPerformed
from python_search.events.run_performed.client import LogRunPerformedClient
from python_search.search_ui.fzf_terminal import FzfInTerminal
from python_search.search_ui.preview import Preview


class PythonSearchCli:
    """
    The command line application, entry point of the program.

    Try to avoid adding direct commands, prefer instead to add objects as parts of functions
    """
    # all commands that are not self-explanatory should not be part of the main api, thus are marked as private.


    configuration: PythonSearchConfiguration

    @staticmethod
    def install_dependencies():
        """install dependenceis"""
        from python_search.init.install_dependencies import InstallDependencies

        InstallDependencies().install_all()

    @staticmethod
    def new_project(project_name: str):
        """Create a new project in the current directory with the given name"""
        from python_search.init.project import Project

        Project().new_project(project_name)

    @staticmethod
    def set_project_location(location: str):
        """Create a new project in the current directory with the given name"""
        from python_search.init.project import Project

        Project().set_current_project(location)

    def __init__(self, configuration: PythonSearchConfiguration = None):
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

    def search(self):
        """
        Opens the Search UI. Main entrypoint of the application
        """
        FzfInTerminal.build_search_ui(self.configuration).run()


    def edit_main(self):
        """Edit the main script"""
        from python_search.entry_capture.edit_content import EditKey

        return EditKey(self.configuration).edit_default()
    def register_new(self):
        """Starts the UI for collecting a new entry into pythonsearch"""
        from python_search.entry_capture.register_new import RegisterNew

        return RegisterNew(self.configuration)

    def edit_key(self, key):
        from python_search.entry_capture.edit_content import EditKey

        return EditKey(self.configuration).edit_key(key, dry_run=False)

    def _copy_entry_content(self, key: str):
        """
        Copies the content of the provided key to the clipboard.
        Used by fzf to provide Ctrl-c functionality.
        """
        from python_search.interpreter.interpreter_matcher import \
            InterpreterMatcher

        InterpreterMatcher.build_instance(self.configuration).clipboard(key)
        LogRunPerformedClient().send(
            RunPerformed(key=key, query_input="", shortcut=False)
        )

    def _copy_key_only(self, key_str: str):
        """
        Copies to clipboard the key
        """
        from python_search.apps.clipboard import Clipboard

        only_key = key_str.split(":")[0]
        Clipboard().set_content(only_key)
        LogRunPerformedClient().send(
            RunPerformed(key=only_key, query_input="", shortcut=False)
        )

    def shortcut_generator(self):
        """Generate shorcuts for all environments"""
        from python_search.shortcut.generator import ShortcutGenerator

        return ShortcutGenerator(self.configuration)
    def _search_edit(self, key=None):
        from python_search.entry_capture.edit_content import EditKey

        result = EditKey(self.configuration).search_entries_directory(key)

        LogRunPerformedClient().send(
            RunPerformed(key=key, query_input="", shortcut=False)
        )
        return result

    def _ranking(self):
        from python_search.ranking.ranking import RankingGenerator

        return RankingGenerator(self.configuration)

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
        Recieves _entries from fzf and show them formatted for the preview window
        """
        Preview().display(entry_text)

    def _infra_report(self):
        from python_search.infrastructure.report import Report

        return Report()


def _error_handler(e):
    import sys
    import traceback

    exc_info = sys.exc_info()
    logging.warning(
        f"Unhandled exception: {e}".join(traceback.format_exception(*exc_info))
    )

    raise e


def _run_key_bin():
    """
    Entry point to run a key
    """
    import fire

    fire.Fire(PythonSearchCli().run_key)


def main():
    import fire

    fire.Fire(PythonSearchCli)
