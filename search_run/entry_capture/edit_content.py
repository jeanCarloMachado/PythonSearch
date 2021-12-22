""" Module responsible for the logic of editing entry files """
import logging
from typing import Optional

from grimoire import s
from grimoire.shell import shell

from search_run.config import config


class EditKey:
    def __init__(self, configuration):
        self.configuration = configuration

    def edit_key(self, key, dry_run=False):
        """
        Edits the configuration files by searching the text
        """
        if not key:
            self._edit_config(self.configuration.get_source_file(), dry_run)
            return

        key = key.split(":")

        if not len(key):
            self._edit_config(self.configuration.get_source_file(), dry_run)
            return

        key = key[0]
        result_shell = shell.run_with_result(
            f"ack '{key}' {self.configuration.get_project_root()} || true"
        )
        if not result_shell:
            logging.info("Could not find match edit main file")
            self._edit_config(self.configuration.get_source_file(), dry_run)
            return

        file, line, *_ = result_shell.split(":")

        self._edit_config(file, line)

    def _edit_config(self, file_name: str, line: Optional[int] = 30, dry_run=False):
        """"edit a configuration file given the name and line """
        cmd: str = (
            f"MY_TITLE='GrimorieSearchRun' runFunction terminal_run 'cd"
            f" {self.configuration.get_project_root()} "
            f"; {config.EDITOR} {file_name} +{line}' "
        )

        if dry_run:
            logging.info(f"Comamnd to edit file: {cmd}")
            return

        s.run(cmd)
