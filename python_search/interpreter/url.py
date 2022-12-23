from python_search.apps.browser import Browser
from python_search.exceptions import CommandDoNotMatchException
from python_search.interpreter.base import BaseInterpreter
from python_search.interpreter.cmd import CmdInterpreter
from python_search.logger import setup_run_key_logger

logger = setup_run_key_logger()


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
        logger.info(f'Processing as url: {self.cmd["url"]}')

        final_cmd = self.cmd
        url = self.cmd["url"]

        final_cmd["cmd"] = Browser().open_shell_cmd(
            url, browser=self.cmd.get("browser")
        )

        logger.info(f"Final URL command={final_cmd}")
        return CmdInterpreter(final_cmd, self.context).interpret_default()

    def copiable_part(self):
        return self.cmd["url"]

    @staticmethod
    def is_url(url_candidate) -> bool:
        return url_candidate.startswith("http")
