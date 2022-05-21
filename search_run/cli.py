from search_run.apps.window_manager import WindowManager
from search_run.config import PythonSearchConfiguration
from search_run.entry_runner import EntryRunner


def error_handler(e):
    from search_run.observability.logger import initialize_systemd_logging

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
        self.configuration = configuration

    def search(self):
        """Main entrypoint of the application"""
        from search_run.search_ui.search import Search

        Search(self.configuration).run()

    def run_key(self):
        return EntryRunner(self.configuration).run_key

    def clipboard_key(self, key):
        """
        Copies the content of the provided key to the clipboard.
        Used by fzf to provide Ctrl-c functionality.
        """
        from search_run.interpreter.interpreter import Interpreter

        Interpreter.build_instance(self.configuration).clipboard(key)

    def edit_key(self, key):
        from search_run.entry_capture.edit_content import EditKey

        return EditKey(self.configuration).edit_key(key, dry_run=False)

    def search_edit(self, key=None):
        from search_run.entry_capture.edit_content import EditKey

        return EditKey(self.configuration).search_entries_directory(key)

    def edit_main(self, key=None):
        """Edit the main script"""
        from search_run.entry_capture.edit_content import EditKey

        return EditKey(self.configuration).edit_default()

    def register_clipboard(self):
        from search_run.entry_capture.register_new import RegisterNew

        return RegisterNew(self.configuration).infer_from_clipboard()

    def register_snippet_clipboard(self):
        from search_run.entry_capture.register_new import RegisterNew

        return RegisterNew(self.configuration).snippet_from_clipboard()

    def register_new(self):
        from search_run.entry_capture.register_new import RegisterNew

        return RegisterNew(self.configuration)

    def export_configuration(self):
        from search_run.shortcut.i3_shortcut_generator import ConfigurationGenerator

        configuration_exporter = ConfigurationGenerator(self.configuration)
        configuration_exporter.export()

    def ranking(self):
        from search_run.ranking.ranking import RankingGenerator

        return RankingGenerator(self.configuration)

    def consumers(self):
        """
        Provides access to the event consumers
        """
        from search_run.events.latest_used_entries import LatestUsedEntries

        class Consumers:
            def latest_used_entries(self):
                LatestUsedEntries().consume()

        return Consumers()

    def features(self):
        from search_run.features import FeatureToggle

        return FeatureToggle()

    def _utils(self):
        """Here commands that are small topics and dont fit the rest"""

        class Utils:
            def __init__(self, configuration):
                self.configuration = configuration

            def hide_launcher(self):
                """hide the search launcher -i2 specific"""
                WindowManager.load_from_environment().hide_window(
                    self.configuration.APPLICATION_TITLE
                )

        return Utils(self.configuration)

    def google_it(self, query):
        from search_run.interpreter.url import Url

        Url(
            {
                "url": f"http://www.google.com/search?q={query}",
            }
        ).interpret_default()

    def next_item_pipeline(self):
        from search_run.ranking.next_item_predictor.pipeline import Pipeline

        return Pipeline
