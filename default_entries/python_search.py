from search_run.config import PythonSearchConfiguration
from search_run.entries_group import EntriesGroup
from search_run.shortcuts import Shortcuts


class PythonSearch(EntriesGroup):
    """
    PythonSearch entries
    """

    commands = {
        "search run search focus or open": {
            "focus_match": PythonSearchConfiguration.APPLICATION_TITLE,
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
        "save clipboard transform clipboard and register to grimoire": {
            "cmd": "search_run register_clipboard",
            "i3_shortcut": Shortcuts.SUPER_R,
        },
        "register snippet search run": {
            "cmd": "search_run register_snippet_clipboard",
            "i3_shortcut": Shortcuts.SUPER_SHIFT_R,
        },
        "register snippet search run": {
            "cmd": "search_run register_snippet_clipboard",
            "i3_shortcut": Shortcuts.SUPER_SHIFT_R,
        },
    }
