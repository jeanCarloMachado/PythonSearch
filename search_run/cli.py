from typing import Optional

from search_run.base_configuration import BaseConfiguration
from search_run.entry_capture.edit_content import EditKey
from search_run.entry_capture.register_new import RegisterNew
from search_run.entry_runner import Runner
from search_run.export_configuration import ConfigurationExporter
from search_run.interpreter.main import Interpreter
from search_run.ranking.nlp import NlpRanking
from search_run.ranking.ranking import Ranking
from search_run.search_ui.search import Search


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
        self.configuration_exporter = ConfigurationExporter(self.configuration)
        self.ranking = Ranking(configuration)
        self.nlp_ranking = NlpRanking(configuration)
        self.export_configuration = self.configuration_exporter.export

    def search(self):
        """ Main entrypoint of the application """
        Search(self.configuration_exporter).run()

    def run_key(self, key, force_gui_mode=False, gui_mode=False, from_shortcut=False):
        return Runner(self.configuration).run(
            key, force_gui_mode, gui_mode, from_shortcut
        )

    def clipboard_key(self, key):
        """
        Copies the content of the provided key to the clipboard.
        Used by fzf to provide Ctrl-c functionality.
        """
        Interpreter.build_instance(self.configuration).clipboard(key)

    def edit_key(self, key, dry_run=False):
        return EditKey(self.configuration).edit_key(key, dry_run=False)

    def register_clipboard(self):
        return RegisterNew(self.configuration).infer_from_clipboard()

    def register_snippet_clipboard(self):
        return RegisterNew(self.configuration).snippet_from_clipboard()

    def r(self, key):
        """
        DEPRECATED: use run instead and use an alias if you are so lazy
        Shorter verion of run key for when lazy
        """
        return self.run_key(key)
