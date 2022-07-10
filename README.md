# PythonSearch

- collect pieces of actionable text in the internet and add them to python dictionaries
- search them using text similarity based on bert and many other ranking methods
- Run the searched entries, with customizeable actions
- add shortcuts to actions
- add custom types and actions

## How to use

Write a python script like this, and call it.

```py
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

from search_run.config import PythonSearchConfiguration
from search_run.cli import PythonSearchCli

config = PythonSearchConfiguration(entries=entries)
PythonSearchCli.setup_from_config(config)

```

## Installation

Installation instructions can be found in the [installation manual](docs/installation.md)

## Legal

This project is licensed under the Apache License, Version 2.0. See [LICENSE](LICENSE.txt) for the full text.
