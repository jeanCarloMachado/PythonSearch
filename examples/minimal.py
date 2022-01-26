#!/usr/bin/env python
import datetime

entries = {
    "open browser": {"url": "https://google.com"},
    # snippets when executed copy the content to the clipboard
    "date current today now copy": {
        # anything can be even python code
        "snippet": datetime.datetime.now().strftime("%Y-%m-%d %H:%M"),
        "i3_shortcut": "Control+Shift+0",
    },
    "matplotlib python import": {"snippet": "import matplotlib.pyplot as plt"},
    # a shell command
    "watch current cpu frequency": {
        "cli_cmd": """
                sudo watch \
                 cat /sys/devices/system/cpu/cpu*/cpufreq/cpuinfo_cur_freq
            """,
    },
    # generate multiple entries based on different values
    **{
        f"get pods for {env}": {"cli_cmd": f"kubectl --context {env} get pods"}
        for env in ["production", "testing"]
    },
}


from search_run.base_configuration import PythonSearchConfiguration

config = PythonSearchConfiguration(entries=entries)

if __name__ == "__main__":
    from search_run.cli import PythonSearchCli

    PythonSearchCli.setup_from_config(config)
