#!/usr/bin/env python3

"""
This is a initial version of python_search _entries to give you a sense of what is possible.
Feel free to delete all the _entries here. You will want to versionate your _entries
"""
import datetime
import os

entries = {
    # NEW_ENTRIES_HERE
    "register new entry": {
        # cmd scripts will be executed in a terminal in the background
        "cmd": "python_search register_new from_clipboard",
    },
    # cli cmds will additional open a new terminal window and execute the  command
    "edit current project _entries source code": {
        "cli_cmd": f"python_search edit_main",
    },
    # urls will be opened in the browser
    "documentation about entities python search": {
        "url": "https://github.com/jeanCarloMachado/PythonSearch/blob/main/docs/entities.md"
    },
    "python search cli source code online reference": {
        "url": "https://shorturl.at/bdeK6"
    },
    # snippets copy  the content of the snippet to the clipboard when executed
    "date current today now copy": {
        "snippet": datetime.datetime.now().strftime("%Y-%m-%d %H:%M"),
        "i3_shortcut": "Control+Shift+0",
    },
    # file will open the file with the standard file handler for the file type in the system
    "edit current selected project _configuration of python search": {
        # you can have multiple projects in paralel with python search
        "file": f"{os.environ['HOME']}/.config/python_search/current_project",
    },
    "get python help function on object": {
        # pythons search is shipped with a multiplataform UI
        # that collects_input to questions and returns the string answered
        "cli_cmd": """python3 -c 'help($(collect_input giveTheObjectName))' """
    },
    # _entries are python code, you can import them from other python scripts
    # or you can generate them dynamically like in the example below
    # here we are generating different _entries for different environments (production, testing, development)
    "help python search manual": {"cli_cmd": "python_search --help"},
    **{
        f"get pods for {env}": {"cli_cmd": f"kubectl --context {env} get pods"}
        for env in ["production", "testing", "development"]
    },
}


from python_search.config import PythonSearchConfiguration

config = PythonSearchConfiguration(entries=entries)
