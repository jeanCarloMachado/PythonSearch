from typing import Optional

from grimoire import s
from grimoire.shell import shell

from search_run.config import MAIN_FILE, PROJECT_ROOT
from search_run.configuration import BaseConfiguration
from search_run.export_configuration import ConfigurationExporter
from search_run.interpreter.main import Interpreter
from search_run.observability.datadog import setup
from search_run.ranking.ranking import Ranking
from search_run.register_new import RegisterNew
from search_run.runner import Runner
from search_run.search import Search


class SearchAndRunCli:
    """
    Entrypoint of the application
    """

    SEARCH_LOG_FILE = "/tmp/search_and_run_log"

    def __init__(self, configuration: Optional[BaseConfiguration] = None):
        self.configuration = configuration
        self.configuration_exporter = ConfigurationExporter(self.configuration)
        self.ranking = Ranking
        setup()

    def search(self):
        """ Main entrypoint of the application """

        def _all_rows_cmd() -> str:
            """returns the shell command to perform to get all get_options_cmd
            and generates the side-effect of createing a new cache file if it does not exist"""
            configuration_file_name = self.configuration_exporter.get_cached_file_name()
            cmd = f' cat "{configuration_file_name}" '
            return cmd

        Search().run(_all_rows_cmd())

    def run_key(self, key, force_gui_mode=False, gui_mode=False, from_shortcut=False):
        return Runner().run(key, force_gui_mode, gui_mode, from_shortcut)

    def export_configuration(self, shortcuts=True):
        self.configuration_exporter.export(shortcuts)

    def clipboard_key(self, key):
        """
        Copies the content to the clipboard of the dmenu option selected
        """
        Interpreter.build_instance().clipboard(key)

    def edit_key(self, key):
        """
        Edits the configuration files by searching the text
        """

        if not key:
            self._edit_config(MAIN_FILE)
            return

        key = key.split(":")

        if not len(key):
            self._edit_config(MAIN_FILE)
            return

        key = key[0]
        result_shell = shell.run_with_result(f"ack '{key}' {PROJECT_ROOT} || true")
        if not result_shell:
            self.edit_config()
            return

        file, line, *_ = result_shell.split(":")

        self._edit_config(file, line)

    def _edit_config(self, file_name: str, line: Optional[int] = 30):
        """"edit a configuration file given the name and line """
        s.run(
            f"MY_TITLE='GrimorieSearchRun' runFunction terminal_run 'vim {file_name} +{line}' ",
        )
        s.run("search_run export_configuration")

    def register_clipboard(self):
        return RegisterNew().infer_from_clipboard()

    def register_snippet_clipboard(self):
        return RegisterNew().snippet_from_clipboard()

    def r(self, key):
        """
        DEPRECATED: use run instead and use an alias if you are so lazy
        Shorter verion of run key for when lazy
        """
        return self.run_key(key)

    def raise_error(self):
        raise Exception("Test exception")
