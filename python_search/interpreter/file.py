import os
from typing import Any

from python_search.context import Context
from python_search.environment import is_mac
from python_search.exceptions import CommandDoNotMatchException
from python_search.interpreter.base import BaseInterpreter
from python_search.interpreter.cmd import CmdInterpreter


class FileInterpreter(BaseInterpreter):
    def __init__(self, cmd: Any, context: Context = None):
        self.context = context
        self.cmd = {}

        if type(cmd) == str:
            self.cmd = {"file": cmd}
            return

        if type(cmd) is dict and "file" in cmd:
            self.cmd = cmd
            return

        if type(cmd) is str and FileInterpreter.file_exists(cmd):
            self.cmd["file"] = cmd
            return

        raise CommandDoNotMatchException(
            f"Not Valid {self.__class__.__name__} command {cmd}"
        )

    def get_executable(self):
        filename, file_extension = os.path.splitext(self.cmd["file"])


        if file_extension in [".py", '.vim']:
            return 'docker_nvim'

        if is_mac():
            return "open"

        if os.path.isdir(self.cmd["file"]):
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
        if executable in ["vim", 'docker_nvim']:
            final_cmd["cli_cmd"] = cmd
        else:
            final_cmd["cmd"] = cmd

        return CmdInterpreter(final_cmd, self.context).interpret_default()

    def copiable_part(self):
        return self.cmd["file"]

    @staticmethod
    def file_exists(candidate: str):
        return os.path.isfile(candidate) or os.path.isdir(candidate)
