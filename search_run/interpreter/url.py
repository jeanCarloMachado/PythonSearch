import logging
import os

from search_run.exceptions import CommandDoNotMatchException
from search_run.interpreter.base import BaseEntry
from search_run.interpreter.cmd import CmdEntry
from search_run.environment import is_mac


class Url(BaseEntry):
    def __init__(self, cmd, context=None):
        self.context = context

        if os.getenv('BROWSER') is None:
            logging.info('BROWSWER environment variable not set! Url commands will not work.')

        if type(cmd) == str and Url.is_url(cmd):
            self.cmd = {"url": cmd}
            return

        if type(cmd) is dict and "url" in cmd:
            self.cmd = cmd
            return

        raise CommandDoNotMatchException(f"Not Valid URL command {cmd}")

    def interpret_default(self):
        logging.info(f'Processing as url: {self.cmd["url"]}')

        if "app_mode" in self.cmd and not is_mac():
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
    def is_url(url_candidate) -> bool:
        return url_candidate.startswith("http")
