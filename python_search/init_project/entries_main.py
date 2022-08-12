#!/usr/bin/env python3

"""
This is the initial version of python_search entries
Feel free to delete all the entries here
You will want to versionate your entries
"""
import datetime

entries = {
    # NEW_ENTRIES_HERE
    "open google": {"url": "https://google.com"},
    # snippets when executed copy the content to the clipboard
    "date current today now copy": {
        # anything can be even python code
        "snippet": datetime.datetime.now().strftime("%Y-%m-%d %H:%M"),
        "i3_shortcut": "Control+Shift+0",
    },
    "register new entry": {
        "cmd": "python_search register_new from_clipboard",
    },
    "os hosts file": {
        "file": '/etc/hosts',
    },
    "edit entries": {
        "cli_cmd": f'python_search edit_main',
    },
    "resources monitoring": {
        # a shell command that open in a new window
        "cli_cmd": "htop",
    },
    'help manual': {'cli_cmd': 'python_search'},
    **{
        # generate multiple entries based on different values
        f"get pods for {env}": {"cli_cmd": f"kubectl --context {env} get pods"}
        for env in ["production", "testing", "local"]
    },
}


from python_search.config import PythonSearchConfiguration
config = PythonSearchConfiguration(entries=entries)

