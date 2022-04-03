import logging
import os
import re

from search_run.exceptions import CommandDoNotMatchException
from search_run.interpreter.base import BaseEntry
from search_run.interpreter.cmd import CmdEntry


class Url(BaseEntry):
    def __init__(self, cmd, context=None):
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

        return CmdEntry(final_cmd, self.context).interpret_default()

    def copiable_part(self):
        return self.cmd["url"]

    @staticmethod
    def is_url(result) -> bool:
        logging.info(f'Trying to match url: {result} "')
        p2 = re.compile("^http.*")
        return p2.search(result)
