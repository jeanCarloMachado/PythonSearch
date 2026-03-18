from __future__ import annotations

import json
import logging
import os
import subprocess
import sys
from typing import Optional

from python_search.apps.clipboard import Clipboard
from python_search.context import Context
from python_search.host_system.system_paths import SystemPaths


class BaseInterpreter:
    """parent of all _interpreters, Cannot instantiate directly"""

    def __init__(self, cmd, context: Optional[Context] = None):
        self.cmd = cmd
        self.context = context

    def default(self) -> None:
        if "ask_confirmation" in self.cmd and not self._confirmed_continue():
            return

        if (
            "call_after" in self.cmd
            or "call_before" in self.cmd
            or "run_before_cmd" in self.cmd
        ):
            logging.info("Enabled sequential execution flag enabled")
            self.context.enable_sequential_execution()

        if "disable_sequential_execution" in self.cmd:
            self.context.disable_sequential_execution()
            logging.info("Disable sequential execution flag enabled")

        self._call_before()
        self._run_before_cmd()
        result = self.interpret_default()
        self._call_after()

        return result

    def _confirmed_continue(self) -> bool:
        from python_search.entry_capture.ask_question_ui import AskQuestion

        result = AskQuestion().ask(
            f"Type (y) if you wanna to proceed to run command: {self.cmd['cmd']}"
        )

        if result == "y":
            return True

        from python_search.apps.notification_ui import send_notification

        send_notification(f"Operation cancelled. Confirmation response was '{result}'")

        return False

    def _call_before(self):
        if "call_before" not in self.cmd:
            return

        logging.info("Call before enabled")
        logging.info(f"Executing post-processing cmd {self.cmd['call_before']}")
        self.context.get_interpreter().default(self.cmd["call_before"])

    def _run_before_cmd(self):
        if "run_before_cmd" not in self.cmd:
            return

        cmd = self.apply_directory(self.cmd["run_before_cmd"])
        logging.info(f"Executing run_before_cmd: {cmd}")
        env = os.environ.copy()
        env["PATH"] = "/opt/homebrew/bin:" + env["PATH"]
        env["PATH"] = SystemPaths.get_python_executable_path() + ":" + env["PATH"]
        env["SHELL"] = "/bin/zsh"
        completed = subprocess.run(
            cmd,
            shell=True,
            env=env,
            stdin=None,
            stdout=sys.stdout,
            stderr=sys.stderr,
        )
        if completed.returncode != 0:
            raise RuntimeError(
                f"run_before_cmd failed with exit code {completed.returncode}: {cmd!r}"
            )

    def _call_after(self):
        if "call_after" not in self.cmd:
            return

        logging.info("Call after enabled")
        logging.info(f"Executing post-processing cmd {self.cmd['call_after']}")
        self.context.get_interpreter().default(self.cmd["call_after"])

    def interpret_default(self):
        raise Exception("Implement me!")

    def interpret_clipboard(self):
        return Clipboard().set_content(self.copiable_part())

    def copiable_part(self):
        return self.serialize()

    def serialize(self):
        return str(self.cmd)

    def to_dict(self):
        return self.cmd

    def serialize_entry(self):
        return json.dumps(self.cmd)

    def apply_directory(self, cmd):
        if "directory" in self.cmd:
            cmd = f'cd {self.cmd["directory"]} ; {cmd}'
        return cmd
