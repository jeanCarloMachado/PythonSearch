from python_search.entries_group import EntriesGroup


class OfficialEntries(EntriesGroup):
    """
    These are the entries supported by default in python search.
    You can keep them always used on your system if you want.

    """

    commands = {
        "install missing dependencies of PythonSearch": {
            "new-window-non-cli": True,
            "cmd": "python_search  install_missing_dependencies",
        },
    }
