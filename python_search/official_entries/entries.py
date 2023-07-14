from python_search.entries_group import EntriesGroup


class OfficialEntries(EntriesGroup):
    """
    These are the entries supported by default in python search.
    You can keep them always used on your system if you want.

    """

    commands = {
        "install missing dependencies of PythonSearch": {
            "cli_cmd": "python_search  install_missing_dependencies",
        },
        "set entries project location": {
            "cli_cmd": 'python_search  set_project_location "$(collect_input --prefill_with_clipboard)"',
        }
    }
