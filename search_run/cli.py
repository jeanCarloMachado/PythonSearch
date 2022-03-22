import os

from search_run.base_configuration import PythonSearchConfiguration
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
        Keep this constructor small and import depependenceis inside the functions
        so they keep being fast
        """
        self.configuration = configuration
        self.run_key = EntryRunner(configuration).run_key

    def search(self):
        """ Main entrypoint of the application """
        from search_run.search_ui.search import Search

        Search(self.configuration).run()

    def clipboard_key(self, key):
        """
        Copies the content of the provided key to the clipboard.
        Used by fzf to provide Ctrl-c functionality.
        """
        from search_run.interpreter.main import Interpreter

        Interpreter.build_instance(self.configuration).clipboard(key)

    def edit_key(self, key):
        from search_run.entry_capture.edit_content import EditKey

        return EditKey(self.configuration).edit_key(key, dry_run=False)

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
        from search_run.configuration_generator import ConfigurationGenerator

        configuration_exporter = ConfigurationGenerator(self.configuration)
        configuration_exporter.export()

    def ranking(self):
        from search_run.ranking.ranking import RankingGenerator

        return RankingGenerator(self.configuration)

    def nlp(self):
        from search_run.ranking.nlp import NlpRanking

        return NlpRanking(self.configuration)

    def consumers(self):
        """ Provides access to the event consumers"""
        from search_run.events.latest_used_entries import LatestUsedEntries

        class Consumers:
            def latest_used_entries(self):
                LatestUsedEntries().consume()

        return Consumers()

    def _utils(self):
        """ Here commands that are small topics and dont fit the rest """

        class Utils:
            def __init__(self, configuration):
                self.configuration = configuration
            def hide_launcher(self):
                """ hide the search launcher -i2 specific """
                os.system(f'sleep 0.1; i3-msg "[title={self.configuration.APPLICATION_TITLE}] move scratchpad"')

        return Utils(self.configuration)
