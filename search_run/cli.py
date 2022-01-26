import os
from typing import Optional

from search_run.base_configuration import (EntriesGroup,
                                           PythonSearchConfiguration)


class PythonSearchCli:
    """
    The command line application, entry point of the program.

    Try to avoid adding direct commands, prefer instead to add objects as parts of functions
    """

    @staticmethod
    def setup_from_config(config: PythonSearchConfiguration):
        try:
            instance = PythonSearchCli(config)
            import fire

            fire.Fire(instance)
        except BaseException as e:
            from search_run.observability.logger import \
                initialize_systemd_logging

            logging = initialize_systemd_logging()
            logging.info(f"Unhandled exception: {e}")
            raise e

    def __init__(self, configuration: Optional[EntriesGroup] = None):
        """
        Keep this constructor small and import depependenceis inside the functions
        so they keep being fast
        """
        self.configuration = configuration

    def search(self):
        """ Main entrypoint of the application """
        from search_run.search_ui.search import Search

        Search().run()

    def run_key(self, key, force_gui_mode=False, gui_mode=False, from_shortcut=False):
        from search_run.entry_runner import Runner

        return Runner(self.configuration).run(
            key, force_gui_mode, gui_mode, from_shortcut
        )

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
        from search_run.ranking.ranking_generator import RankingGenerator

        return RankingGenerator(self.configuration)

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
            def hide_launcher(self):
                """ hide the search launcher -i3 specific """
                os.system('sleep 0.3; i3-msg "[title=launcher] move scratchpad"')

        return Utils()
