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
    # use search run to help you to learn language
    "letter ending viele grusse": {
            "snippet": "Viele Grüße",
            "created_at": "2021-10-26T13:15:25.559320",
    },
    'zeigt': {'snippet': 'indicates / show / demonstrate', 'language': 'German', 'created_at': '2022-01-24T13:02:43.959548'},
    # generate multiple entries based on different values
    **{
        f"get pods for {env}": {"cli_cmd": f"kubectl --context {env} get pods"}
        for env in ["production", "testing", "local"]
    },
}


# this configuration file contains all customizeable options for search run
from search_run.base_configuration import PythonSearchConfiguration
config = PythonSearchConfiguration(entries=entries)

if __name__ == "__main__":
    from search_run.cli import PythonSearchCli

    PythonSearchCli.setup_from_config(config)
