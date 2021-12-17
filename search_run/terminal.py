import logging

from grimoire.shell import shell
import os


class Terminal:
    DEFAULT_TITLE = "RandomTerminal"

    def start_new(
            self, cmd, title=None, hold_terminal_open_on_end=True, return_command=False
    ):
        if hold_terminal_open_on_end:
            cmd = f" {cmd}"

        title_part = ""
        if title:
            title_part = f"MY_TITLE='{title}' "

        #final_cmd = f"{title_part}runFunction terminal_run '{cmd}'"
        os.system(f'kitty -T "{title}" bash -c "{cmd}" ')

        if return_command:
            return final_cmd

        logging.info(final_cmd)
        return shell.run_command_no_wait(final_cmd)
