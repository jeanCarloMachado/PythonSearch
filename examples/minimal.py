from datetime import datetime

from fire import Fire

from search_run.base_configuration import BaseConfiguration
from search_run.cli import SearchAndRunCli

class Configuration(BaseConfiguration):
    commands = {
        "open browser": {"url": "https://google.com"},
        # snippets to the clipboard
        "date current today now copy": {
            # anything can be
            "snippet": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "i3_shortcut": "Control+Shift+0",
        },
        # a shell command
        "watch current cpu frequency": {
            "new-window-non-cli": True,
            "cmd": """
                    sudo watch \
                     cat /sys/devices/system/cpu/cpu*/cpufreq/cpuinfo_cur_freq
                """,
        },
    }


instance = SearchAndRunCli(Configuration())


if __name__ == "__main__":
    Fire(instance)
