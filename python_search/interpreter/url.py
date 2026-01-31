import os
import subprocess

from python_search.apps.browser import Browser
from python_search.exceptions import CommandDoNotMatchException
from python_search.host_system.system_paths import SystemPaths
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

        # Run preprocessing command if specified
        if "run_before_cmd" in self.cmd:
            self._run_before_cmd()

        final_cmd = self.cmd
        url = self.cmd["url"]

        final_cmd["cmd"] = Browser().open_shell_cmd(
            url,
            browser=self.cmd.get("browser"),
            focus_title=self.cmd.get("app_focus_title"),
        )

        logger.info(f"Final URL command={final_cmd}")
        return CmdInterpreter(final_cmd, self.context).interpret_default()

    def _run_before_cmd(self):
        """Execute a preprocessing command before opening the URL. Waits for completion by default."""
        before_cmd = self.cmd["run_before_cmd"]
        logger.info(f"Running preprocessing command: {before_cmd}")

        env = os.environ.copy()
        env["PATH"] = "/opt/homebrew/bin:" + env["PATH"]
        env["PATH"] = SystemPaths.get_python_executable_path() + ":" + env["PATH"]
        env["SHELL"] = "/bin/zsh"

        result = subprocess.run(
            before_cmd,
            shell=True,
            env=env,
        )

        logger.info(f"Preprocessing command finished with return code: {result.returncode}")

    def copiable_part(self):
        return self.cmd["url"]

    @staticmethod
    def is_url(url_candidate) -> bool:
        return url_candidate.startswith("http")
