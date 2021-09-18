from __future__ import annotations

import json

from grimoire.desktop.clipboard import Clipboard
from grimoire.desktop.dmenu import Dmenu
from grimoire.desktop.window import Window
from grimoire.logging import logging
from grimoire.notification import send_notification
from grimoire.shell import shell

from search_run.context import Context


class BaseInterpreter:
    """parent of all interpreters"""

    def __init__(self, cmd, context: Context):
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
        self.interpret_default()
        self._call_after()

    def _confirmed_continue(self) -> bool:
        result = Dmenu(
            title=f"Type (y) if you wanna to proceed to run command: {self.cmd['cmd']}"
        ).rofi()

        if result == "y":
            return True

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

    def serialize_entry(self):
        return json.dumps(self.cmd)

    def wrap_launch_on_i3(self, cmd):
        # if "workspace" in self.cmd:
        #     return f"i3 'workspace {self.cmd['workspace']}; exec {cmd}'"

        return cmd

    def apply_directory(self, cmd):
        if "directory" in self.cmd:
            cmd = f'cd {self.cmd["directory"]} ; {cmd}'
        return cmd

    def try_to_focus(self) -> bool:

        if "focus_match" not in self.cmd:
            return False

        focus_identifier = self.cmd["focus_match"]

        match_type = self.cmd["match_type"] if "match_type" in self.cmd else "title"

        if "focus_match_only_class" in self.cmd:
            match_type = "class"

        if Window().focus(focus_identifier, match_type=match_type):
            logging.info(
                "No window after focusing? Maybe it is resized small, try to close the window after focusing."
            )
            if shell.run(
                f"i3-msg '[{match_type}=\"{focus_identifier}\"] scratchpad show'"
            ):
                shell.run('sleep 0.5; i3-msg "floating disable; floating enable"')
            else:
                shell.run(
                    f"i3-msg '[{match_type}=\"{focus_identifier}\"] scratchpad show'"
                )

            return True

        return False
