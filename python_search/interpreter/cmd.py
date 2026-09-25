import os
import shlex
import subprocess
import sys
import tempfile
from typing import Optional

from python_search.apps.notification_ui import send_notification
from python_search.apps.terminal import get_terminal
from python_search.context import Context
from python_search.exceptions import CommandDoNotMatchException
from python_search.host_system.system_paths import SystemPaths
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

        if isinstance(cmd, str):
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
        cmd = self.apply_directory(self.cmd["cmd"])

        cmd = self._try_to_wrap_in_terminal(cmd)

        logger.info(f"Command to run: {cmd}")
        result = self._execute(cmd)
        logger.info(f"Result finished: {result}")
        return self.return_result(result)

    def _try_to_wrap_in_terminal(self, cmd):
        if WRAP_IN_TERMINAL not in self.cmd and WRAP_IN_TERMINAL not in os.environ:
            return cmd

        logger.info("Running it in a new terminal")

        hold_terminal = False if "not_hold_terminal" in self.cmd else True
        cmd = get_terminal().wrap_cmd_into_terminal(
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

        env = os.environ
        # add homebrew path to the path
        env["PATH"] = "/opt/homebrew/bin:" + env["PATH"]
        # add /usr/local/bin to the path (e.g. for code, brew-installed binaries)
        env["PATH"] = "/usr/local/bin:" + env["PATH"]
        # add python search executable path to the path
        env["PATH"] = SystemPaths.get_python_executable_path() + ":" + env["PATH"]
        # append the monorepo conda env bin path so its CLI binaries (e.g. `monorepo`) are found
        env["PATH"] = env["PATH"] + ":" + os.path.expanduser(
            "~/miniconda3/envs/python313/bin"
        )
        env["SHELL"] = "/bin/zsh"

        # cli_cmd entries are wrapped in a visible terminal (errors show there);
        # plain cmd entries run silently, so we notify on failure (and, with
        # notify_output, on success too).
        #
        # This wait-and-notify has to happen *inside* the detached shell
        # process, not in a Python thread here: run_key is a one-shot CLI
        # that returns and exits almost immediately after this call, well
        # before a command doing real work (e.g. a network call) finishes.
        # A background thread would just get killed with it. The subprocess
        # itself, spawned with start_new_session=True, already reliably
        # outlives this process (that's the whole point of detaching it), so
        # it's the only thing that can safely wait for its own completion.
        wrapped_in_terminal = WRAP_IN_TERMINAL in self.cmd
        if not wrapped_in_terminal:
            cmd = self._wrap_with_notifications(cmd)

        p = subprocess.Popen(
            cmd,
            shell=True,
            # add path to the system path
            env=env,
            stdin=None,
            stdout=sys.stdout,
            stderr=sys.stderr,
            close_fds=True,
            # make sure the process does not die when python search dies
            start_new_session=True,
        )

        return {"pid": p.pid}

    def _wrap_with_notifications(self, cmd):
        # notify_output (default False): always notify with the full stdout/stderr,
        # not just on failure. Only applies to plain "cmd" entries (not "cli_cmd"),
        # since a terminal-wrapped command's output lives in a separate Terminal
        # window we never capture.
        notify_output = self.cmd.get("notify_output", False)
        notify_send = SystemPaths.get_binary_full_path("notify_send")
        output_path = tempfile.mktemp(suffix=".log")

        success_notify = (
            f'msg=$(cat {shlex.quote(output_path)}); '
            f'[ -z "$msg" ] && msg="(no output)"; '
            f'{shlex.quote(notify_send)} "$msg"'
            if notify_output
            else "true"
        )

        return (
            # a subshell, not a `{ ...; }` group: a bare `exit` inside cmd
            # must only end the wrapped command, not this whole wrapper
            # script (which still needs to run the notify/cleanup steps below).
            f"( {cmd} ) > {shlex.quote(output_path)} 2>&1; "
            f"__rc=$?; "
            f'if [ "$__rc" -ne 0 ]; then '
            f"msg=$(grep -v '^[[:space:]]*$' {shlex.quote(output_path)} | tail -1); "
            f'[ -z "$msg" ] && msg="exit code $__rc"; '
            f'{shlex.quote(notify_send)} "Entry Failed: $msg"; '
            f"else {success_notify}; fi; "
            f"rm -f {shlex.quote(output_path)}"
        )

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
