""" Module responsible for the logic of editing entry files """
import logging
import subprocess
from typing import Optional

from python_search.apps.terminal import Terminal
from python_search.core_entities import Key
from python_search.search_ui.kitty import get_kitty_cmd


class EntriesEditor:
    """
    Set of commands to edit the _entries
    """

    def __init__(self, configuration = None):
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
        cmd = f"ack -i '{key}' {self.configuration.get_project_root()} --py || true"
        logging.info(f"Command: {cmd}")
        result_shell = subprocess.check_output(cmd, shell=True, text=True)

        if not result_shell:
            logging.info("Could not find match edit main file")
            self.edit_default()
            return

        file, line, *_ = result_shell.split(":")
        print(f"Editing file and line {file}, {line}")

        self._edit_config(file, line)


    def edit_default(self):
        import os
        os.system(f"open -a pycharm '{self.configuration.get_project_root() + '/entries_main.py'}'")

    def _edit_config(self, file_name: str, line: Optional[int] = 30, dry_run=False):
        """
        edit a configuration file given the name and line
        """

        # @ todo make this editor generic

        terminal = Terminal()
        cmd: str = (
            f" {get_kitty_cmd()} {terminal.GENERIC_TERMINAL_PARAMS} {terminal.get_background_color()} bash -c 'cd"
            f" {self.configuration.get_project_root()} "
            f"; {self._get_open_text_editor_command(file_name, line)} "
        )
        print(cmd)

        if dry_run:
            logging.info(f"Command to edit file: {cmd}")
            return

        import os

        os.system(cmd)

    def _get_open_text_editor_command(self, file, line):
        if self.configuration.get_text_editor() == "vim":
            return f"{self.configuration.get_text_editor()} {file} +{line}'"
        elif self.configuration.get_text_editor() == "docker_nvim":
            return f"{self.configuration.get_text_editor()} {file} --line={line}'"
        else:
            # if is not a known editor just open the file
            return f"{self.configuration.get_text_editor()} {file}"


def main():
    import fire
    fire.Fire(EntriesEditor)
