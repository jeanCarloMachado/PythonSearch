# PythonSearch

- collect pieces of actionable text in the internet and add them to python dictionaries
- search them using text similarity based on bert and many other ranking methods
- Run the searched entries, with customizeable actions
- add shortcuts to actions
- add custom types and actions


## How to use

Write a python script like this, and call it.

```py

from datetime import datetime


from search_run.base_configuration import BaseConfiguration
from search_run.cli import SearchAndRunCli
from fire import Fire


class Configuration(BaseConfiguration):
    commands = {
        # a browser url
        "search browser": {"url": "https://google.com"},
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


Fire(SearchAndRunCli(Configuration()))

```

## Installation

Installation instructions can be found in the [installation manual](docs/installation.md)


## Legal

This project is licensed under the Apache License, Version 2.0. See [LICENSE](LICENSE.txt) for the full text.
