import os
from typing import Any

from search_run.context import Context
from search_run.exceptions import CommandDoNotMatchException
from search_run.interpreter.base import BaseInterpreter
from search_run.interpreter.cmd import CmdInterpreter


class FileInterpreter(BaseInterpreter):
    def __init__(self, cmd: Any, context: Context):
        self.context = context
        self.cmd = {}

        if type(cmd) is dict and "file" in cmd:
            self.cmd = cmd
            return

        if type(cmd) is str and (os.path.isfile(cmd) or os.path.isdir(cmd)):
            self.cmd["file"] = cmd
            return

        raise CommandDoNotMatchException(
            f"Not Valid {self.__class__.__name__} command {cmd}"
        )

    def get_executable(self):
        if os.path.isdir(self.cmd["file"]):
            return "nautilus"

        executable = "vim"

        filename, file_extension = os.path.splitext(self.cmd["file"])

        if file_extension == ".php":
            executable = "phpstormn"
        elif file_extension == ".pdf":
            # executable = "okular"
            executable = "zathura"
        elif file_extension == ".py":
            executable = "vim"
        elif file_extension == ".ipynb":
            executable = "pycharm"

        return executable

    def interpret_default(self):
        executable = self.get_executable()

        cmd = f'{executable} "{self.cmd["file"]}"'

        final_cmd = self.cmd
        if executable == "vim":
            final_cmd["cli_cmd"] = cmd
        else:
            final_cmd["cmd"] = cmd

        return CmdInterpreter(final_cmd, self.context).interpret_default()

    def copiable_part(self):
        return self.cmd["file"]
