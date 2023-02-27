import os
from typing import Any

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

        if type(cmd) == str:
            self.cmd = {"file": cmd}

        if type(cmd) == dict and "file" not in cmd:
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
        filename, file_extension = os.path.splitext(self.cmd["file"])

        if file_extension in [".py", ".vim", ".", ".rc", ".yaml", ".yml", ".conf"]:
            return "docker_nvim"

        if os.path.isdir(self.cmd["file"]):
            if is_mac():
                return "open"
            return "nautilus"

        if file_extension == ".pdf":
            return "zathura"

        elif file_extension == ".ipynb":
            return "pycharm"

        return "docker_nvim"

    def interpret_default(self):
        executable = self.get_executable()

        cmd = f'{executable} "{self.cmd["file"]}"'

        final_cmd = self.cmd
        if executable in ["vim", "docker_nvim"]:
            final_cmd["cli_cmd"] = cmd
        else:
            final_cmd["cmd"] = cmd
            # final_cmd["new-window-non-cli"] = True

        return CmdInterpreter(final_cmd, self.context).interpret_default()

    def copiable_part(self):
        return self.cmd["file"]

    @staticmethod
    def file_exists(candidate: str):
        return os.path.isfile(candidate) or os.path.isdir(candidate)
