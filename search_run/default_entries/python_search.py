from search_run.base_configuration import EntriesGroup


class PythonSearch(EntriesGroup):
    """
    PythonSearch entries
    """

    commands = {
        "search run search focus or open": {
            "focus_match": "PythonSearchWindow",
            "cmd": "nice -19 search_run search",
        },
        "start search run search capslock": {
            "focus_match": "launcher",
            "cmd": "nice -19 search_run search",
            "i3_shortcut": "Mod3+space",
        },
        "recompute rank search run cleaning the cache regenerate": {
            "new-window-non-cli": True,
            "cmd": "search_run ranking generate --recompute_ranking=True",
        },
        "compute rerank search run": {
            "new-window-non-cli": True,
            "cmd": "search_run ranking recompute_rank",
        },
    }
