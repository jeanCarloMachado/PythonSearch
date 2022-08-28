from __future__ import annotations

import json
import logging
from typing import Optional

from python_search.apps.clipboard import Clipboard
from python_search.apps.window_manager import I3
from python_search.context import Context
from python_search.environment import is_mac


class BaseInterpreter:
    """parent of all _interpreters, Cannot instantiate directly"""

    def __init__(self, cmd, context: Optional[Context] = None):
        self.cmd = cmd
        self.context = context

    def default(self) -> None:
        if "ask_confirmation" in self.cmd and not self._confirmed_continue():
            return

        if "call_after" in self.cmd or "call_before" in self.cmd:
            logging.info("Enabled sequential execution flag enabled")
            self.context.enable_sequential_execution()

        if "disable_sequential_execution" in self.cmd:
            self.context.disable_sequential_execution()
            logging.info("Disable sequential execution flag enabled")

        self._call_before()
        result = self.interpret_default()
        self._call_after()

        return result

    def _confirmed_continue(self) -> bool:
        from python_search.entry_capture.ui import AskQuestion

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

    def try_to_focus(self) -> bool:
        """
        Focus on the window if it is already running and return True.
        If it is not running, return False.
        """

        if "focus_match" not in self.cmd:
            return False

        if is_mac():
            print("Will not try to focus as this is not supported yet")
            return False

        return I3().focus_on_window_with_title(self.cmd["focus_match"])
