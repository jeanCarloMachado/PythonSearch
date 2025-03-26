"""Module responsible for the logic of editing entry files"""

import logging
import subprocess
from typing import Optional

from python_search.apps.terminal import KittyTerminal
from python_search.core_entities import Key
from python_search.search.search_ui.kitty_for_search_ui import get_kitty_cmd


class EntriesEditor:
    """
    Open an ide to edit the entries
    """

    ACK_PATH = '/opt/homebrew/bin/ack'

    def __init__(self, configuration=None):
        if not configuration:
            from python_search.configuration.loader import ConfigurationLoader

            configuration = ConfigurationLoader().load_config()
        self.configuration = configuration

    def edit_key(self, key_expr: str):
        """
        Edits the configuration files by searching the text
        """

        key = str(Key.from_fzf(key_expr))
        print(f"Editing key {key}")
        if not key:
            self.edit_default()
            return

        if not len(key):
            print("Editing default")
            self.edit_default()
            return

        # needs to be case-insensitive search
        cmd = f"{EntriesEditor.ACK_PATH} -i '{key}' {self.configuration.get_project_root()} --python || true"
        logging.info(f"Command: {cmd}")
        result_shell = subprocess.check_output(cmd, shell=True, text=True)

        if not result_shell:
            print("Could not find match edit main file, output: ", result_shell)
            self.edit_default()
            return

        file, line, *_ = result_shell.split(":")
        print(f"Editing file and line {file}, {line}")

        self._edit_file(file, line)

    def edit_default(self):
        import os

        os.system(
            f"kitty vim '{self.configuration.get_project_root() + '/entries_main.py'}'"
        )

    def _edit_file(self, file_name: str, line: Optional[int] = 30, dry_run=False):
        """
        edit a configuration file given the name and line
        """

        # @ todo make this editor generic

        terminal = KittyTerminal()
        cmd: str = (
            f" {terminal.get_kitty_cmd()} {terminal.GENERIC_TERMINAL_PARAMS} bash -c 'cd"
            f" {self.configuration.get_project_root()} "
            f"; {self._get_open_text_editor_command(file_name, line) }"
        )
        print(cmd)

        if dry_run:
            logging.info(f"Command to edit file: {cmd}")
            return

        import os

        os.system(cmd)

    def _get_open_text_editor_command(self, file, line):
        # vim only supported
        return f"vim {file} +{line}'"


def main():
    import fire
    fire.Fire(EntriesEditor)


if __name__ == "__main__":
    main()
