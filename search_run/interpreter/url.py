import logging

from grimoire.desktop.browser import Browser
from search_run.interpreter.base import (
    BaseInterpreter,
)
from search_run.exceptions import CommandDoNotMatchException
from search_run.interpreter.cmd import CmdInterpreter
from grimoire.string import Url


class UrlInterpreter(BaseInterpreter):
    def __init__(self, cmd, context):
        self.context = context
        if type(cmd) == str and Url.is_url(cmd):
            self.cmd = {"url": cmd}
            return

        if type(cmd) is dict and "url" in cmd:
            self.cmd = cmd
            return

        raise CommandDoNotMatchException(f"Not Valid URL command {cmd}")

    def interpret_default(self):
        logging.info(f'Processing as url: {self.cmd["url"]}')

        b = Browser()
        app_mode = False
        if "app_mode" in self.cmd:
            app_mode = True

        cmd = b.open_get_command(self.cmd["url"], app_mode=app_mode)

        logging.info(f"Final command={cmd}")

        final_cmd = self.cmd
        final_cmd["cmd"] = cmd

        return CmdInterpreter(final_cmd, self.context).interpret_default()

    def copiable_part(self):
        return self.cmd["url"]
