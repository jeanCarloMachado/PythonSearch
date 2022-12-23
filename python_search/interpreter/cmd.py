from typing import Optional

# @ todo remove this dependencies on grimoire
from python_search.apps.notification_ui import send_notification
from python_search.apps.terminal import Terminal
from python_search.context import Context
from python_search.exceptions import CommandDoNotMatchException
from python_search.interpreter.base import BaseInterpreter
from python_search.logger import setup_run_key_logger

# @todo find a better name
WRAP_IN_TERMINAL = "new-window-non-cli"

logger = setup_run_key_logger()


class CmdInterpreter(BaseInterpreter):
    """
    Represents a bash command entry. It can be used anywhere to run bash commends.
    """

    def __init__(self, cmd, context: Optional[Context] = None):
        """ """
        self.context = context

        if type(cmd) == str:
            self.cmd = {WRAP_IN_TERMINAL: True, "cmd": cmd}
            return

        if WRAP_IN_TERMINAL in cmd and "cmd" in cmd:
            self.cmd = cmd
            return

        if "cli_cmd" in cmd:
            self.cmd = cmd
            self.cmd["cmd"] = cmd["cli_cmd"]
            self.cmd[WRAP_IN_TERMINAL] = True
            return

        if "cmd" in cmd:
            self.cmd = cmd
            return

        raise CommandDoNotMatchException.not_valid_command(self, cmd)

    def interpret_default(self):
        if self.try_to_focus():
            return

        cmd = self.apply_directory(self.cmd["cmd"])

        if "high_priority" in self.cmd:
            cmd = f"nice -19 {cmd}"

        if "directory" in self.cmd:
            cmd = f'cd {self.cmd["directory"]} && {cmd}'

        if WRAP_IN_TERMINAL in self.cmd:
            cmd = self._try_to_wrap_in_terminal(cmd)

        logger.info(f"Command to run: {cmd}")
        result = self._execute(cmd)
        logger.info(f"Result finished: {result}")
        return self.return_result(result)

    def _try_to_wrap_in_terminal(self, cmd):
        if WRAP_IN_TERMINAL not in self.cmd:
            return cmd

        logger.info("Running it in a new terminal")

        hold_terminal = False if "not_hold_terminal" in self.cmd else True
        cmd = Terminal().wrap_cmd_into_terminal(
            cmd,
            title=self._get_window_title(),
            hold_terminal_open_on_end=hold_terminal,
        )
        logger.info(f"Command to run: {cmd}")

        return cmd

    def _get_window_title(self):
        if "window_title" in self.cmd:
            return self.cmd["window_title"]

        title = self.cmd["cmd"]
        if "focus_match" in self.cmd:
            title = self.cmd["focus_match"]

        return remove_special_chars(title, [" "])

    def _execute(self, cmd):
        logger.info(f"To run as subprocess: {cmd}")

        import subprocess
        import sys

        p = subprocess.Popen(
            cmd,
            shell=True,
            stdin=None,
            stdout=sys.stdout,
            stderr=sys.stderr,
            close_fds=True,
            # make sure the process does not die when python search dies
            start_new_session=True,
        )

        return {"pid": p.pid}

    def return_result(self, result):
        if "notify-result" in self.cmd:
            send_notification(result)

        return result

    def copiable_part(self):
        return self.cmd["cmd"]


def remove_special_chars(string, exceptions=[]):
    """
    Remove all special chars from strings except if they are one of the exceptions
    """
    result = "".join(e for e in string if e.isalnum() or e in exceptions)
    return result
