""" Module responsible for the logic of editing entry files """
import logging
import subprocess
from typing import Optional

from python_search.apps.terminal import Terminal
from python_search.interpreter.cmd import CmdInterpreter


class EditKey:
    """
    Set of commands to edit the _entries
    """

    def __init__(self, configuration):
        self.configuration = configuration

    def edit_key(self, key, dry_run=False):
        """
        Edits the _configuration files by searching the text
        """
        print(f"Editing key {key}")
        if not key:
            self.edit_default()
            return

        key = key.split(":")

        if not len(key):
            self.edit_default()
            return

        key = key[0]
        # needs to be case insensitive search
        cmd = f"ack -i '{key}' {self.configuration.get_project_root()} --py || true"
        logging.info(f"Command: {cmd}")
        result_shell = subprocess.check_output(cmd, shell=True, text=True)

        if not result_shell:
            logging.info("Could not find match edit main file")
            self._edit_config(self.configuration.get_source_file(), dry_run)
            return

        file, line, *_ = result_shell.split(":")
        print(f"Editng file and line {file}, {line}")

        self._edit_config(file, line)

    def search_entries_directory(self, key=None):
        entry = {
            "cli_cmd": f"fzf_directory.sh {self.configuration.get_project_root()}",
            "directory": self.configuration.get_project_root(),
        }

        CmdInterpreter(entry).interpret_default()

    def edit_default(self):
        self._edit_config(self.configuration.get_project_root() + "/entries_main.py")

    def _edit_config(self, file_name: str, line: Optional[int] = 30, dry_run=False):
        """
        edit a configuration file given the name and line
        """

        # @ todo make this editor generic

        cmd: str = (
            f"MY_TITLE='GrimorieSearchRun' kitty {Terminal.GENERIC_TERMINAL_PARAMS} bash -c 'cd"
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
        if self.configuration.get_text_editor() == 'vim':
            return f"{self.configuration.get_text_editor()} {file} +{line}'"
        elif self.configuration.get_text_editor() == 'docker_nvim':
            return f"{self.configuration.get_text_editor()} {file} --line={line}'"
        else:
            # if is not a known editor just open the file
            return f"{self.configuration.get_text_editor()} {file}"
