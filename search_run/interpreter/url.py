import logging
import os
from grimoire.string import Url

from search_run.apps.browser import Browser
from search_run.exceptions import CommandDoNotMatchException
from search_run.interpreter.base import BaseInterpreter
from search_run.interpreter.cmd import CmdInterpreter


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

        if 'app_mode' in self.cmd:
            shell_cmd = f"{os.getenv('BROWSER')} --app='{self.cmd['url']}'"
        else:
            shell_cmd = f"{os.getenv('BROWSER')} '{self.cmd['url']}'"

        logging.info(f"Final command={shell_cmd}")

        final_cmd = self.cmd
        final_cmd["cmd"] = shell_cmd

        return CmdInterpreter(final_cmd, self.context).interpret_default()

    def copiable_part(self):
        return self.cmd["url"]
