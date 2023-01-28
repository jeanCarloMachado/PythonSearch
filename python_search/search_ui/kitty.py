import os

from python_search.apps.terminal import Terminal
from python_search.configuration.configuration import PythonSearchConfiguration
from python_search.environment import is_mac
from python_search.search_ui.fzf import Fzf


class FzfInKitty:
    """
    Renders the search ui using fzf + termite terminal
    """

    FONT_SIZE: int = 15
    _default_window_size = (800, 400)

    configuration: PythonSearchConfiguration

    def __init__(self, configuration: PythonSearchConfiguration):
        custom_window_size = configuration.get_window_size()
        self.width = (
            custom_window_size[0]
            if custom_window_size
            else self._default_window_size[0]
        )
        self.height = (
            custom_window_size[1]
            if custom_window_size
            else self._default_window_size[1]
        )

        self.title = configuration.APPLICATION_TITLE
        self.configuration = configuration

        import logging
        import sys

        logger = logging.getLogger(name="search_ui")
        logger.addHandler(logging.StreamHandler(sys.stdout))
        logger.setLevel(logging.DEBUG)

        self._logger = logger
        self._fzf = Fzf(configuration)

    def run(self) -> None:
        self._focus_or_launch()

    def _focus_or_launch(self):
        """
        Focuses the terminal if it is already open
        """
        result = os.system(f"{get_kitty_cmd()} @ --to unix:/tmp/mykitty focus-window")
        if result != 0 or not os.path.exists("/tmp/mykitty"):
            self._launch()

    def _launch(self) -> None:
        internal_cmd = self._fzf.get_cmd()
        font = "FontAwesome"
        if is_mac():
            font = "Pragmata Pro"
        terminal = Terminal()

        launch_cmd = f"""nice -19 {get_kitty_cmd()} \
        --title {self.title} \
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
        -o initial_window_width={self.width}  \
        -o initial_window_height={self.height} \
        -o font_family="{font}" \
        {terminal.get_background_color()} \
        -o font_size={FzfInKitty.FONT_SIZE} \
        {terminal.GLOBAL_TERMINAL_PARAMS} \
         {internal_cmd}
        """
        self._logger.info(f"Command performed:\n {internal_cmd}")
        result = os.system(launch_cmd)
        if result != 0:
            raise Exception("Search run fzf projection failed")



def get_kitty_cmd() -> str:
    if is_mac():
        return "/Applications/kitty.app/Contents/MacOS/kitty"
    return "kitty"

if __name__ == "__main__":
    import fire

    fire.Fire()
