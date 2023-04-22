import os

import logging
import sys

from python_search.environment import is_mac


class FzfInKitty:
    """
    Renders the search ui using fzf + termite terminal
    """

    FONT_SIZE: int = 16
    _default_window_size = (800, 400)

    _configuration = None

    def __init__(self, configuration=None):
        logger = logging.getLogger(name="search_ui")
        logger.addHandler(logging.StreamHandler(sys.stdout))
        logger.setLevel(logging.DEBUG)
        self._logger = logger

        if not configuration:
            from python_search.configuration.loader import ConfigurationLoader

            configuration = ConfigurationLoader().load_config()
        self._configuration = configuration
        custom_window_size = configuration.get_window_size()
        self._width = (
            custom_window_size[0]
            if custom_window_size
            else self._default_window_size[0]
        )
        self._height = (
            custom_window_size[1]
            if custom_window_size
            else self._default_window_size[1]
        )

        self._title = configuration.APPLICATION_TITLE

        self._FONT = "FontAwesome" if not is_mac() else "Menlo"
        from python_search.search_ui.fzf import Fzf

        self._fzf = Fzf(configuration)

    @staticmethod
    def run() -> None:
        if not FzfInKitty.try_to_focus():
            FzfInKitty().launch()

    @staticmethod
    def try_to_focus():
        """
        Focuses the terminal if it is already open
        """
        if not os.path.exists("/tmp/mykitty"):
            return False

        result = os.system(FzfInKitty.focus_kitty_command())

        return result == 0

    @staticmethod
    def focus_or_open(configuration):
        if not FzfInKitty.try_to_focus():
            FzfInKitty(configuration).launch()

    @staticmethod
    def focus_kitty_command():
        return f"{get_kitty_cmd()} @ --to unix:/tmp/mykitty focus-window"

    def launch(self) -> None:
        from python_search.apps.terminal import Terminal

        terminal = Terminal()

        fzf_cmd = self._fzf.get_cmd()

        launch_cmd = f"""nice -19 {get_kitty_cmd()} \
        --title {self._title} \
        --listen-on unix:/tmp/mykitty \
        -o allow_remote_control=yes \
        -o draw_minimal_borders=no \
        -o window_padding_width=0  \
        -o placement_strategy=center \
        -o window_border_width=0 \
        -o window_padding_width=0 \
        -o hide_window_decorations=titlebar-only \
        -o background_opacity=1 \
        -o active_tab_title_template=none \
        -o initial_window_width={self._width}  \
        -o initial_window_height={self._height} \
        -o font_family="{self._FONT}" \
        {terminal.get_background_color()} \
        -o font_size={FzfInKitty.FONT_SIZE} \
        {terminal.GLOBAL_TERMINAL_PARAMS} \
         {fzf_cmd}
        """
        result = os.system(launch_cmd)
        if result != 0:
            raise Exception("Search run fzf projection failed")


def get_kitty_cmd() -> str:
    if is_mac():
        return "/Applications/kitty.app/Contents/MacOS/kitty"
    return "kitty"


def main():
    import fire

    fire.Fire(FzfInKitty)


if __name__ == "__main__":
    main()
