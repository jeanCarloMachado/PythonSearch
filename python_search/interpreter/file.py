import os
from typing import Any

from python_search.host_system.system_paths import SystemPaths
from python_search.context import Context
from python_search.environment import is_mac
from python_search.exceptions import CommandDoNotMatchException
from python_search.interpreter.base import BaseInterpreter
from python_search.interpreter.cmd import CmdInterpreter


class FileInterpreter(BaseInterpreter):
    """
    Interprets files
    """

    def __init__(self, cmd: Any, context: Context = None):
        self.context = context
        self.cmd = cmd

        if isinstance(cmd, str):
            self.cmd = {"file": cmd}

        if isinstance(cmd, dict) and "file" not in cmd:
            raise CommandDoNotMatchException(
                f"Not Valid {self.__class__.__name__} command {cmd}"
            )

        if self.cmd["file"].startswith("/") or FileInterpreter.file_exists(
            self.cmd["file"]
        ):
            return

        raise CommandDoNotMatchException(
            f"Not Valid {self.__class__.__name__} command {cmd}"
        )

    def get_executable(self):
        if not os.path.exists(SystemPaths.VIM_BINNARY):
            raise Exception("Vim binnary not found in path {SystemPaths.VIM_BINNARY}")
        return SystemPaths.VIM_BINNARY

    def interpret_default(self):
        executable = self.get_executable()

        cmd = f'{executable} "{self.cmd["file"]}"'

        final_cmd = {}
        final_cmd["cli_cmd"] = cmd

        return CmdInterpreter(final_cmd, self.context).interpret_default()

    def copiable_part(self):
        return self.cmd["file"]

    @staticmethod
    def file_exists(candidate: str):
        return os.path.isfile(candidate) or os.path.isdir(candidate)
