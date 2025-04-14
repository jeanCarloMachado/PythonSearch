import os

import logging
import sys
from python_search.apps.terminal import KittyTerminal
from python_search.host_system.system_paths import SystemPaths
from python_search.environment import is_mac
import sys

SOCKET_PATH = "/tmp/mykitty"
class KittyForSearchUI:
    """
    Renders the search ui using fzf + termite terminal
    """

    _DEFAULT_WINDOW_SIZE = ('86c', '10c')

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
            else self._DEFAULT_WINDOW_SIZE[0]
        )
        self._height = (
            custom_window_size[1]
            if custom_window_size
            else self._DEFAULT_WINDOW_SIZE[1]
        )

        self._title = configuration.APPLICATION_TITLE

    def launch(self) -> None:
        """
        Entry point for the application to launch the search ui
        """

        cmd = self.get_kitty_complete_cmd()
        self._logger.debug(f"Launching kitty with cmd: {cmd}")
        result = os.system(cmd)
        if result != 0:
            raise Exception("Failed: " + str(result))
    
    def get_kitty_complete_cmd(self) -> str:
        terminal = KittyTerminal()
        from python_search.apps.theme.theme import get_current_theme
        theme = get_current_theme()
        return f"""{self.get_kitty_cmd()} \
        --title {self._title} \
        --listen-on unix:{SOCKET_PATH} \
        -o allow_remote_control=yes \
        -o window_padding_width=0  \
        -o placement_strategy=center \
        -o window_border_width=0 \
        -o window_padding_width=0 \
        -o hide_window_decorations=titlebar-only \
        -o background_opacity=0.9 \
        -o active_tab_title_template=none \
        -o initial_window_width={self._width}  \
        -o initial_window_height={self._height} \
        -o background={theme.backgroud} \
        -o foreground={theme.text} \
        -o font_size="{theme.font_size}" \
        {terminal.GLOBAL_TERMINAL_PARAMS} \
         {SystemPaths.BINARIES_PATH}/term_ui &
        """

    @staticmethod
    def try_to_focus() -> bool:
        """
        Focuses the terminal if it is already open
        """
        if not os.path.exists(SOCKET_PATH):
            print(f"File {SOCKET_PATH} not found")
            return False

        cmd = f'{SystemPaths.KITTY_BINNARY} @ --to unix:{SOCKET_PATH} focus-window '
        print("Cmd: ", cmd)
        result = os.system(cmd)
        print(result, "Type: ", type(result))
        sys.exit(0)

        return result == 0

    @staticmethod
    def focus_or_open(configuration=None):
        if os.environ.get("SKIP_FOCUS"):
            KittyForSearchUI(configuration).launch()
            return

        print("Trying to focus")
        if KittyForSearchUI.try_to_focus():
            print("Focused instead of launching")
            os.exit(0)
            return

        KittyForSearchUI(configuration).launch()

    def get_kitty_cmd(self) -> str:
        return SystemPaths.KITTY_BINNARY


def main():
    import fire

    fire.Fire(KittyForSearchUI)

def get_kitty_cmd() -> str:
    return SystemPaths.KITTY_BINNARY


if __name__ == "__main__":
    main()
