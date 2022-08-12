#!/usr/bin/env python3

"""
This is a working sample of the entries module.
You will want to versionate your entries using git.
"""
import datetime

entries = {
    # NEW_ENTRIES_HERE
    "open browser": {"url": "https://google.com"},
    # snippets when executed copy the content to the clipboard
    "date current today now copy": {
        # anything can be even python code
        "snippet": datetime.datetime.now().strftime("%Y-%m-%d %H:%M"),
        "i3_shortcut": "Control+Shift+0",
    },
    "matplotlib python import": {"snippet": "import matplotlib.pyplot as plt"},
    # a shell command
    "resources monitoring": {
        "cli_cmd": "htop",
    },
    # generate multiple entries based on different values
    **{
        f"get pods for {env}": {"cli_cmd": f"kubectl --context {env} get pods"}
        for env in ["production", "testing", "local"]
    },
}


# this configuration file contains all customizable options for search run
from python_search.config import PythonSearchConfiguration

config = PythonSearchConfiguration(entries=entries)

if __name__ == "__main__":
    from python_search.cli import PythonSearchCli

    PythonSearchCli.setup_from_config(config)
