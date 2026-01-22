import os

import logging
import sys
from python_search.apps.terminal import KittyTerminal
from python_search.host_system.system_paths import SystemPaths
from python_search.host_system.display_detection import AdaptiveWindowSizer

SOCKET_PATH = "/tmp/mykitty"


class KittyForSearchUI:
    """
    Renders the search ui using fzf + termite terminal
    """

    _DEFAULT_WINDOW_SIZE = ("86c", "10c")

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

        # Determine window size based on configuration
        custom_window_size = configuration.get_window_size()

        if custom_window_size:
            # Use explicitly configured size
            self._width = custom_window_size[0]
            self._height = custom_window_size[1]
        elif configuration.should_use_adaptive_sizing():
            # Use adaptive sizing based on display characteristics
            self._width, self._height = self._get_adaptive_window_size(configuration)
        else:
            # Fall back to default size
            self._width = self._DEFAULT_WINDOW_SIZE[0]
            self._height = self._DEFAULT_WINDOW_SIZE[1]

        self._title = configuration.APPLICATION_TITLE

    def _get_adaptive_window_size(self, configuration) -> tuple[str, str]:
        """Get adaptive window size based on display characteristics"""
        try:
            # Check for environment variable override first
            env_width = os.environ.get("PYTHON_SEARCH_WINDOW_WIDTH")
            env_height = os.environ.get("PYTHON_SEARCH_WINDOW_HEIGHT")
            env_preset = os.environ.get("PYTHON_SEARCH_WINDOW_PRESET")

            if env_width and env_height:
                self._logger.debug(f"Using environment variable window size: {env_width}x{env_height}")
                return env_width, env_height

            sizer = AdaptiveWindowSizer()

            # Check environment preset override
            if env_preset:
                presets = sizer.get_preset_sizes()
                if env_preset in presets:
                    self._logger.debug(f"Using environment preset: {env_preset}")
                    return presets[env_preset]
                else:
                    self._logger.warning(f"Unknown environment preset '{env_preset}', " f"using adaptive sizing")

            # Check if a preset is specified in configuration
            preset = configuration.get_window_size_preset()
            if preset:
                presets = sizer.get_preset_sizes()
                if preset in presets:
                    self._logger.debug(f"Using configuration preset: {preset}")
                    return presets[preset]
                else:
                    self._logger.warning(f"Unknown preset '{preset}', using adaptive sizing")

            # Use adaptive sizing
            self._logger.debug("Using adaptive window sizing")
            return sizer.get_adaptive_window_size()

        except Exception as e:
            self._logger.error(f"Failed to get adaptive window size: {e}")
            # Fall back to default size
            return self._DEFAULT_WINDOW_SIZE

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
        cmd_parts = [
            self.get_kitty_cmd(),
            f"--title {self._title}",
            f"--listen-on unix:{SOCKET_PATH}",  # noqa: E231
            "-o allow_remote_control=yes",
            "-o window_padding_width=0",
            "-o placement_strategy=center",
            "-o window_border_width=0",
            "-o window_padding_width=0",
            "-o hide_window_decorations=titlebar-only",
            "-o background_opacity=0.9",
            "-o active_tab_title_template=none",
            f"-o initial_window_width={self._width}",
            f"-o initial_window_height={self._height}",
            f"-o background={theme.backgroud}",
            f"-o foreground={theme.text}",
            f'-o font_size="{theme.font_size}"',
            terminal.GLOBAL_TERMINAL_PARAMS,
            f"{SystemPaths.get_binary_full_path('term_ui')} &",
        ]
        return " ".join(cmd_parts)

    @staticmethod
    def try_to_focus() -> bool:
        """
        Focuses the terminal if it is already open
        """
        if not os.path.exists(SOCKET_PATH):
            print(f"File {SOCKET_PATH} not found")
            return False

        cmd = f"{SystemPaths.KITTY_BINNARY} @ --to " f"unix:{SOCKET_PATH} focus-window"  # noqa: E231
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
