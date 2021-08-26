from typing import Optional

from grimoire.desktop.dmenu import Dmenu
from grimoire.shell import shell
from search_run.search import Search
from search_run.register_new import RegisterNew
from search_run.run_key import RunKey
from search_run.config import PROJECT_ROOT, MAIN_FILE
from search_run.interpreter.main import Interpreter
from search_run.configuration import BaseConfiguration
from search_run.export_configuration import ConfigurationExporter
from search_run.ranking.ranking import Ranking
from grimoire import s


class SearchAndRunCli:
    """
    Entrypoint of the application
    """

    SEARCH_LOG_FILE = "/tmp/search_and_run_log"

    def __init__(self, configuration: Optional[BaseConfiguration] = None):
        self.configuration = configuration
        self.configuration_exporter = ConfigurationExporter(self.configuration)
        self.ranking = Ranking

    def export_configuration(self, shortcuts=True):
        self.configuration_exporter.export(shortcuts)

    def search(self):
        Search().run(self._all_rows_cmd())

    def dmenu(self):
        self.search()

    def dmenu_clipboard(self):
        """
        Copies the content to the clipboard of the dmenu option selected
        """
        ui = Dmenu()
        result = ui.rofi(self._all_rows_cmd())
        Interpreter.build_instance().clipboard(result)

    def dmenu_edit(self):
        ui = Dmenu(title="Edit search run:")
        result = ui.rofi(self._all_rows_cmd())

        if not result:
            self.edit_config()
            return

        result = result.split(":")

        if not len(result):
            self.edit_config()
            return

        key = result[0]

        result_shell = shell.run_with_result(f"ack '{key}' {PROJECT_ROOT} || true")
        if not result_shell:
            self.edit_config()
            return

        file, line, *_ = result_shell.split(":")

        self.edit_config(file, line)

    def edit_config(self, file_name: Optional[str] = None, line: Optional[int] = None):
        if not file_name:
            file_name = MAIN_FILE
        if not line:
            line = 30

        s.run(
            f"MY_TITLE='GrimorieSearchRun' runFunction terminal_run 'vim {file_name} +{line}' ",
        )
        s.run("search_run export_configuration")

    def register_clipboard(self):
        return RegisterNew().infer_from_clipboard()

    def register_snippet_clipboard(self):
        return RegisterNew().snippet_from_clipboard()

    def run_key(self, key, force_gui_mode=False, gui_mode=False, from_shortcut=False):
        return RunKey().run(key, force_gui_mode, gui_mode, from_shortcut)

    def r(self, key):
        """ Shorter verion of run key for when lazy"""
        return self.run_key(key)

    def tail_log(self):
        s.run(f"tail -f " + SearchAndRunCli.SEARCH_LOG_FILE)

    def _all_rows_cmd(self) -> str:
        """returns the shell command to perform to get all get_options_cmd
        and generates the side-effect of createing a new cache file if it does not exist"""
        configuration_file_name = self.configuration_exporter.get_cached_file_name()
        cmd = f' cat "{configuration_file_name}" '
        return cmd

    def raise_error(self):
        raise Exception("Test exception")
