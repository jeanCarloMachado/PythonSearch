#!/usr/bin/env python
print("New seearch_run![")

from typing import Optional

from grimoire import s
from grimoire.desktop.clipboard import Clipboard
from grimoire.desktop.dmenu import Dmenu
from search_run.application.dmenu_run import DmenuRun
from search_run.export_configuration import ConfigurationExporter
from search_run.ranking import Ranking
from search_run.application.register_new import RegisterNew
from search_run.application.run_key import RunKey
from search_run.config import MAIN_FILE, PROJECT_ROOT
from search_run.domain.interpreter.main import Interpreter
from grimoire.shell import shell


class SearchAndRunCli:
    """
    Converts a dict in the format: {"keyIdentifer: {commandDetails, "keyIndentifier2": {commandDetails}
    to executable magic in python
    """

    SEARCH_LOG_FILE = "/tmp/search_and_run_log"

    def __init__(self):
        self.configuration_exporter = ConfigurationExporter
        self.ranking = Ranking

    def export_configuration(self, shortcuts=True):
        self.configuration_exporter().export(shortcuts)

    def dmenu(self):
        DmenuRun().run(self._all_rows_cmd())

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

    def interpret_clipboard(self):
        """
        Rather than opening-dmenu sends the content of the clipboard for the interpreter

        """
        Interpreter.build_instance().default(Clipboard().get_content())

    def fzf(self):
        ui = Dmenu()
        result = ui.fzf(self._all_rows_cmd())

        Interpreter.build_instance().default(result)


    def run_key(self, key, force_gui_mode=False, gui_mode=False, from_shortcut=False):
        return RunKey().run(key, force_gui_mode, gui_mode, from_shortcut)

    def r(self, key):
        """ Shorter verion of run key for when lazy"""
        return self.run_key(key)

    def repeat_last_run(self):
        from grimoire.event_sourcing.message import MessageBroker

        message = MessageBroker("run_key_command_performed").consume_last()
        self.run_key(message["key"])

    def tail_log(self):
        s.run(f"tail -f " + SearchAndRunCli.SEARCH_LOG_FILE)

    def _all_rows_cmd(self):
        configuration_file_name = ConfigurationExporter.get_cached_file_name()
        cmd = f' cat "{configuration_file_name}" '
        return cmd

    def raise_error(self):
        raise Exception("Test exception")


if __name__ == "__main__":

    from fire import Fire
    Fire(SearchAndRunCli)
