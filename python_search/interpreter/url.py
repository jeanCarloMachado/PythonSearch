from python_search.apps.browser import Browser
from python_search.exceptions import CommandDoNotMatchException
from python_search.interpreter.base import BaseInterpreter
from python_search.interpreter.cmd import CmdInterpreter
from python_search.logger import setup_run_key_logger

logger = setup_run_key_logger()


class UrlInterpreter(BaseInterpreter):
    def __init__(self, cmd, context=None):
        self.context = context

        if isinstance(cmd, str) and UrlInterpreter.is_url(cmd):
            self.cmd = {"url": cmd}
            return

        if isinstance(cmd, dict) and "url" in cmd:
            self.cmd = cmd
            return

        raise CommandDoNotMatchException(f"Not Valid URL command {cmd}")

    def interpret_default(self):
        logger.info(f'Processing as url: {self.cmd["url"]}')

        final_cmd = self.cmd
        url = self.cmd["url"]

        final_cmd["cmd"] = Browser().open_shell_cmd(
            url,
            app_mode=self.cmd.get("app_mode"),
            browser=self.cmd.get("browser"),
            focus_title=self.cmd.get("focus_match") or self.cmd.get("app_focus_title"),
        )

        logger.info(f"Final URL command={final_cmd}")
        return CmdInterpreter(final_cmd, self.context).interpret_default()

    def _run_before_cmd(self):
        """Execute a preprocessing command before opening the URL."""
        if not self.cmd.get("run_before_cmd"):
            return

        before_cmd = self.cmd["run_before_cmd"]
        logger.info(f"Running preprocessing command: {before_cmd}")
        super()._run_before_cmd()
        logger.info("Preprocessing command finished successfully")

    def copiable_part(self):
        return self.cmd["url"]

    @staticmethod
    def is_url(url_candidate) -> bool:
        return url_candidate.startswith("http")
