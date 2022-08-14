import os


class Terminal:
    """
    Terminal abstraction for Python Search
    The underlying terminal is kitty but we could support more in the future if needed
    """

    # these parameters are applied both to all kitty windows of pythons search
    # including the generic params and the python search main window
    GLOBAL_TERMINAL_PARAMS = " -o remember_window_size=yes -o placement_strategy=center -o confirm_os_window_close=0  -o remember_window_size=n -o macos_quit_when_last_window_closed=yes "

    # this parameters are applied to cli_cmd terminals

    DEFAULT_HEIGHT = 500
    DEFAULT_WIDTH = 900
    GENERIC_TERMINAL_PARAMS = f" {GLOBAL_TERMINAL_PARAMS} -o initial_window_width={DEFAULT_WIDTH} -o initial_window_height={DEFAULT_HEIGHT} -o font_size=13 "

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
            f'kitty {hold} {Terminal.GENERIC_TERMINAL_PARAMS} -T "{title}" {cmd} '
        )

        return final_cmd
