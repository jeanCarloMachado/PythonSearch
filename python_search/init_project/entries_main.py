#!/usr/bin/env python3

"""
This is the initial version of python_search entries
Feel free to delete all the entries here
You will want to versionate your entries
"""
import datetime

entries = {
    # NEW_ENTRIES_HERE
    "register new entry": {
        "cmd": "python_search register_new from_clipboard",
    },
    "documentation about entities python search": {
        "url": "https://github.com/jeanCarloMachado/PythonSearch/blob/main/docs/entities.md"
    },
    "python search cli online reference": {
        "url": "https://shorturl.at/bdeK6"
    },
    "edit entries python file": {
        "cli_cmd": f'python_search edit_main',
    },
    # snippets when executed copy the content to the clipboard
    "date current today now copy": {
        # anything can be even python code
        "snippet": datetime.datetime.now().strftime("%Y-%m-%d %H:%M"),
        "i3_shortcut": "Control+Shift+0",
    },
    "os hosts file": {
        "file": '/etc/hosts',
    },
    'google it': {'cmd': 'python_search google_it "$(collect_input GoogleTerm)"'},
    # python search also offers a collect_input binary that asks questions via ui and return the answer
    'python help function on object': {'cli_cmd': """python3 -c 'help($(collect_input giveTheObjectName))' """},
    'man lsof': {'new-window-non-cli': True, 'cmd': ' man lsof', 'created_at': '2022-08-07T09:32:35.911249'},
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

