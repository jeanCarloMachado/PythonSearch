import datetime

from search_run.base_configuration import BaseConfiguration
from search_run.cli import PythonSearchCli


class Configuration(BaseConfiguration):
    commands = {
        "open browser": {"url": "https://google.com"},
        # snippets when executed copy the content to the clipboard
        "date current today now copy": {
            # anything can be even python code
            "snippet": datetime.datetime.now().strftime("%Y-%m-%d %H:%M"),
            "i3_shortcut": "Control+Shift+0",
        },
        # a shell command
        "watch current cpu frequency": {
            "cli_cmd": """
                    sudo watch \
                     cat /sys/devices/system/cpu/cpu*/cpufreq/cpuinfo_cur_freq
                """,
        },
    }


if __name__ == "__main__":
    PythonSearchCli.setup_from_config(Configuration())
