#!/usr/bin/env python
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
    # uses the application itself to register new entries from the clipboard
    "register new entry programatically": {
        "cmd": "minimal.py register_clipboard",
    },
    # use search run to help you to learn language
    "letter ending viele grusse": {
        "snippet": "Viele Grüße",
    },
    "zeigt": {"snippet": "indicates / show / demonstrate", "language": "German"},
}


# this configuration file contains all customizeable options for search run
from search_run.config import PythonSearchConfiguration

config = PythonSearchConfiguration(entries=entries)

if __name__ == "__main__":
    from search_run.cli import PythonSearchCli

    PythonSearchCli.setup_from_config(config)
