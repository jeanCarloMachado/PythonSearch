from typing import Optional

from search_run.base_configuration import BaseConfiguration
from search_run.configuration_generator import ConfigurationGenerator
from search_run.interpreter.main import Interpreter
from search_run.ranking.ranking_generator import RankingGenerator


class SearchAndRunCli:
    """
    The command line application, entry point of the program.
    Python Fire wraps this class.
    """

    def __init__(self, configuration: Optional[BaseConfiguration] = None):
        """
        :param configuration:
        :param entries: the setted up entries
        """

        self.configuration = configuration
        self.configuration_exporter = ConfigurationGenerator(self.configuration)
        self.ranking = RankingGenerator(configuration)
        self.export_configuration = self.configuration_exporter.export

    def search(self):
        """ Main entrypoint of the application """
        from search_run.search_ui.search import Search

        Search(self.configuration_exporter).run()

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


def setup(config: BaseConfiguration):
    instance = SearchAndRunCli(config)
    import fire
    fire.Fire(instance)