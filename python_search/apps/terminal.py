import os

from python_search.environment import is_mac


class Terminal:
    """
    Terminal abstraction for search run
    """

    DEFAULT_TERMINAL_PARAMS = " -o confirm_os_window_close=0  -o macos_quit_when_last_window_closed=yes -o remember_window_size=n -o initial_window_width=1300 -o initial_window_height=700 -o font_size=13 "

    def wrap_cmd_into_terminal(
        self, cmd, title=None, hold_terminal_open_on_end=True
    ) -> str:
        """
        wraps the command in a terminal but does not execute it
        """
        shell = (
            os.environ["PYTHON_SEARCH_CUSTOM_SHELL"]
            if "PYTHON_SEARCH_CUSTOM_SHELL" in os.environ
            else "bash"
        )
        shell = "/bin/bash"
        cmd = f'{shell} -c "{cmd}"'

        hold = ""
        if hold_terminal_open_on_end:
            hold = " --hold "

        final_cmd = (
            f'kitty {hold} {Terminal.DEFAULT_TERMINAL_PARAMS} -T "{title}" {cmd} '
        )

        return final_cmd
