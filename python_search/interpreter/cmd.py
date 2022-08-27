import logging
from typing import Optional

from grimoire.shell import shell
from grimoire.string import remove_special_chars

# @ todo remove this dependencies on grimoire
from python_search.apps.notification_ui import send_notification
from python_search.apps.terminal import Terminal
from python_search.context import Context
from python_search.exceptions import CommandDoNotMatchException
from python_search.interpreter.base import BaseInterpreter

# @todo find a better name
WRAP_IN_TERMINAL = "new-window-non-cli"


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

        if "tmux" in self.cmd:
            cmd = f'tmux new -s "{self._get_window_title()}" {cmd} '

        if WRAP_IN_TERMINAL in self.cmd:
            cmd = self._try_to_wrap_in_terminal(cmd)

        print(f"Command to run: {cmd}")
        result = self._execute(cmd)
        print(f"Result finished: {result}")
        return self.return_result(result)

    def _try_to_wrap_in_terminal(self, cmd):
        if WRAP_IN_TERMINAL not in self.cmd:
            return cmd

        logging.info("Running it in a new terminal")

        hold_terminal = False if "not_hold_terminal" in self.cmd else True
        cmd = Terminal().wrap_cmd_into_terminal(
            cmd,
            title=self._get_window_title(),
            hold_terminal_open_on_end=hold_terminal,
        )
        logging.info(f"Command to run: {cmd}")

        return cmd

    def _get_window_title(self):
        if "window_title" in self.cmd:
            return self.cmd["window_title"]

        title = self.cmd["cmd"]
        if "focus_match" in self.cmd:
            title = self.cmd["focus_match"]

        return remove_special_chars(title, [" "])

    def _execute(self, cmd):
        logging.info(f"To run: {cmd}")

        hold_terminal = False if "not_hold_terminal" in self.cmd else True
        if (
            self.context
            and self.context.is_group_command()
            and not self.context.should_execute_sequentially()
        ) or not hold_terminal:
            return shell.run_command_no_wait(cmd)

        if self.context and self.context.should_execute_sequentially():
            return shell.run_with_result(cmd)

        import subprocess

        p = subprocess.Popen(
            cmd,
            shell=True,
            stdin=None,
            stdout=None,
            stderr=None,
            close_fds=True,
        )

        return {"pid": p.pid}

    def return_result(self, result):
        if "notify-result" in self.cmd:
            send_notification(result)

        return result

    def copiable_part(self):
        return self.cmd["cmd"]
