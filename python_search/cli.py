import logging

from python_search.apps.window_manager import WindowManager
from python_search.config import ConfigurationLoader, PythonSearchConfiguration
from python_search.entry_runner import EntryRunner
from python_search.environment import is_mac
from python_search.search_ui.preview import Preview


def error_handler(e):
    from python_search.observability.logger import initialize_systemd_logging

    logging = initialize_systemd_logging()
    import sys
    import traceback

    exc_info = sys.exc_info()
    logging.warning(
        f"Unhandled exception: {e}".join(traceback.format_exception(*exc_info))
    )

    raise e


class PythonSearchCli:
    """
    The command line application, entry point of the program.

    Try to avoid adding direct commands, prefer instead to add objects as parts of functions
    """

    configuration: PythonSearchConfiguration

    @staticmethod
    def setup_from_config(config: PythonSearchConfiguration):
        try:
            instance = PythonSearchCli(config)
            import fire

            fire.Fire(instance)
        except BaseException as e:
            error_handler(e)

    def __init__(self, configuration: PythonSearchConfiguration = None):
        """
        Keep this constructor small and import dependencies inside the functions
        so they keep being fast
        """
        if not configuration:
            logging.debug("No configuration provided, using default")
            configuration = ConfigurationLoader().load_config()

        self.configuration = configuration

    def search(self):
        """Main entrypoint of the application"""
        from python_search.search_ui.search import Search

        Search(self.configuration).run()

    def run_key(self):
        import sys

        print(sys.version_info)
        return EntryRunner(self.configuration).run_key

    def copy_entry_content(self, key: str):
        """
        Copies the content of the provided key to the clipboard.
        Used by fzf to provide Ctrl-c functionality.
        """
        from python_search.interpreter.interpreter import Interpreter

        Interpreter.build_instance(self.configuration).clipboard(key)

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

    def edit_main(self, key=None):
        """Edit the main script"""
        from python_search.entry_capture.edit_content import EditKey

        return EditKey(self.configuration).edit_default()

    def register_clipboard(self):
        from python_search.entry_capture.register_new import RegisterNew

        return RegisterNew(self.configuration).infer_from_clipboard()

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
        from python_search.interpreter.url import Url

        Url(
            {
                "url": f"http://www.google.com/search?q={query}",
            }
        ).interpret_default()

    def next_item_pipeline(self):
        from python_search.ranking.next_item_predictor.pipeline import Pipeline

        return Pipeline

    def infra_report(self):
        from python_search.infrastructure.report import Report

        return Report()

    def capture_input(self):
        from python_search.apps.capture_input import CollectInput

        return CollectInput.launch


def main():
    import fire

    fire.Fire(PythonSearchCli)
