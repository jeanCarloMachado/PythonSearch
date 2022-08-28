import logging

from python_search.apps.window_manager import WindowManager
from python_search.config import ConfigurationLoader, PythonSearchConfiguration
from python_search.entry_runner import EntryRunner
from python_search.environment import is_mac
from python_search.search_ui.preview import Preview


class PythonSearchCli:
    """
    The command line application, entry point of the program.

    Try to avoid adding direct commands, prefer instead to add objects as parts of functions
    """

    configuration: PythonSearchConfiguration

    @staticmethod
    def setup_from_config(config: PythonSearchConfiguration):
        """Initialized the cli with the main configuration object"""
        try:
            instance = PythonSearchCli(config)
            import fire

            fire.Fire(instance)
        except BaseException as e:
            _error_handler(e)

    @staticmethod
    def new_project(project_name: str):
        """Create a new project in the current directory with the given name"""
        from python_search.init_project import InitializeProject

        InitializeProject().initialize(project_name)

    def __init__(self, configuration: PythonSearchConfiguration = None):
        """
        Keep this constructor small and import dependencies inside the functions
        so they keep being fast
        """
        if not configuration:
            logging.debug("No configuration provided, using default")
            try:
                configuration = ConfigurationLoader().load_config()
            except Exception as e:
                print(f"Did not find any config to load, error: {e}")
                import traceback

                print(traceback.format_exc())

                return

        self.configuration = configuration
        self.run_key = EntryRunner(self.configuration).run

    def search(self):
        """
        Opens the Search UI. Main entrypoint of the application
        """
        from python_search.search_ui.search import Search

        Search(self.configuration).run()


    def copy_entry_content(self, key: str):
        """
        Copies the content of the provided key to the clipboard.
        Used by fzf to provide Ctrl-c functionality.
        """
        from python_search.interpreter.interpreter_matcher import \
            InterpreterMatcher

        InterpreterMatcher.build_instance(self.configuration).clipboard(key)

    def copy_key_only(self, key_str: str):
        """
        Copies to clipboard the key
        """
        from python_search.apps.clipboard import Clipboard

        Clipboard().set_content(key_str.split(":")[0])

    def edit_key(self, key):
        from python_search.entry_capture.edit_content import EditKey

        return EditKey(self.configuration).edit_key(key, dry_run=False)

    def search_edit(self, key=None):
        from python_search.entry_capture.edit_content import EditKey

        return EditKey(self.configuration).search_entries_directory(key)

    def edit_main(self):
        """Edit the main script"""
        from python_search.entry_capture.edit_content import EditKey

        return EditKey(self.configuration).edit_default()

    def register_clipboard(self):
        from python_search.entry_capture.register_new import RegisterNew

        return RegisterNew(self.configuration).launch_ui()

    def register_new(self):
        from python_search.entry_capture.register_new import RegisterNew

        return RegisterNew(self.configuration)

    def shortcut_generator(self):
        """Generate shorcuts for all environments"""
        from python_search.shortcut.generator import ShortcutGenerator

        return ShortcutGenerator(self.configuration)

    def ranking(self):
        from python_search.ranking.ranking import RankingGenerator

        return RankingGenerator(self.configuration)

    def consumers(self):
        """
        Provides access to the event consumers
        """
        from python_search.events.latest_used_entries import LatestUsedEntries

        class Consumers:
            def latest_used_entries(self):
                LatestUsedEntries().consume()

        return Consumers()

    def features(self):
        """Feature toggle system"""
        from python_search.features import FeatureToggle

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

            def preview_entry(self, entry_text: str):
                """
                Recieves entries from fzf and show them formatted for the preview window
                """
                Preview().display(entry_text)

        return Utils(self.configuration)

    def google_it(self, query):
        from python_search.interpreter.url import UrlInterpreter

        UrlInterpreter(
            {
                "url": f"http://www.google.com/search?q={query}",
            }
        ).interpret_default()

    def _infra_report(self):
        from python_search.infrastructure.report import Report

        return Report()


def _error_handler(e):
    from python_search.observability.logger import initialize_systemd_logging

    logging = initialize_systemd_logging()
    import sys
    import traceback

    exc_info = sys.exc_info()
    logging.warning(
        f"Unhandled exception: {e}".join(traceback.format_exception(*exc_info))
    )

    raise e

def _run_key_bin():
    import fire
    fire.Fire(PythonSearchCli().run_key)

def main():
    import fire

    fire.Fire(PythonSearchCli)
