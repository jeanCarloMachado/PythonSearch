import logging
import os


class Terminal:
    """Terminal abstraction for search run"""

    DEFAULT_TITLE = "SearchRunTerminal"

    @staticmethod
    def run_command(cmd) -> bool:
        """runs a shell command  raise an exception on failure"""
        message = f'=> Command to run: "{cmd}"'
        logging.debug(message)

        result = os.system(cmd)
        success = result == 0

        return success

    def wrap_cmd_into_terminal(
        self, cmd, title=None, hold_terminal_open_on_end=True
    ) -> str:
        """
        wraps the command in a terminal but does not execute it
        """
        if hold_terminal_open_on_end:
            cmd = f" {cmd}"

        final_cmd = f'kitty -T "{title}" bash -c "{cmd}" '

        return final_cmd
