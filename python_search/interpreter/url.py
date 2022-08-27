import logging

from python_search.apps.browser import Browser
from python_search.exceptions import CommandDoNotMatchException
from python_search.interpreter.base import BaseInterpreter
from python_search.interpreter.cmd import CmdInterpreter


class UrlInterpreter(BaseInterpreter):
    def __init__(self, cmd, context=None):
        self.context = context

        if type(cmd) == str and UrlInterpreter.is_url(cmd):
            self.cmd = {"url": cmd}
            return

        if type(cmd) is dict and "url" in cmd:
            self.cmd = cmd
            return

        raise CommandDoNotMatchException(f"Not Valid URL command {cmd}")

    def interpret_default(self):
        logging.info(f'Processing as url: {self.cmd["url"]}')

        app_mode = self.cmd["app_mode"] if "app_mode" in self.cmd else False
        shell_cmd: str = Browser().open_cmd(self.cmd["url"], app_mode)

        final_cmd = self.cmd
        final_cmd["cmd"] = shell_cmd

        print(f"Final command={final_cmd}")
        return CmdInterpreter(final_cmd, self.context).interpret_default()

    def copiable_part(self):
        return self.cmd["url"]

    @staticmethod
    def is_url(url_candidate) -> bool:
        return url_candidate.startswith("http")
