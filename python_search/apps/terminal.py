import os
from python_search.configuration.loader import ConfigurationLoader


class KittyTerminal:
    """
    Terminal abstraction for Python Search
    The underlying terminal is kitty but we could support more in the future if needed
    """

    DEFAULT_HEIGHT = '50c'
    DEFAULT_WIDTH = '120c'
    FONT_SIZE = 15


    # these parameters are applied both to all kitty windows of pythons search
    # including the generic params and the python search main window
    GLOBAL_TERMINAL_PARAMS = " -o remember_window_size=yes " + \
    " -o confirm_os_window_close=0 " + \
    " -o remember_window_size=n " + \
    " -o resize_in_steps=1 " + \
    " -o macos_quit_when_last_window_closed=yes "

    GENERIC_TERMINAL_PARAMS = f" {GLOBAL_TERMINAL_PARAMS} " + \
    f" -o initial_window_width={DEFAULT_WIDTH} " + \
    f" -o initial_window_height={DEFAULT_HEIGHT} " + \
    f" -o font_size={FONT_SIZE} "


    def __init__(self):
        self.configuration = ConfigurationLoader().get_config_instance()

    def wrap_cmd_into_terminal(
        self, cmd, title=None, hold_terminal_open_on_end=True
    ) -> str:
        """
        wraps the command in a terminal but does not execute it
        """
        shell = "/bin/zsh"
        # quoting here makes a big difference
        cmd = f"{shell} -c '{cmd}'"

        hold = ""
        if hold_terminal_open_on_end:
            hold = " --hold "


        final_cmd = f'{self.get_kitty_cmd()} {hold} {KittyTerminal.GENERIC_TERMINAL_PARAMS} -T "{title}" {cmd} '

        return final_cmd


    def get_kitty_cmd(self):
        from python_search.search.search_ui.kitty_for_search_ui import get_kitty_cmd
        return get_kitty_cmd()
