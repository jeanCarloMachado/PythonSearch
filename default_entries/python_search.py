from search_run.config import PythonSearchConfiguration
from search_run.entries_group import EntriesGroup
from search_run.shortcuts import Shortcuts


class PythonSearch(EntriesGroup):
    """
    PythonSearch entries
    """

    commands = {
        "search run search focus or open": {
            "description": "Starts python search only once and reuse the same session",
            "focus_match": PythonSearchConfiguration.APPLICATION_TITLE,
            "cmd": "nice -19 search_run search",
            "gnome_shortcut": "<Alt>space",
        },
        "save entry from clipboard inferring type": {
            "description": "Register to search run a string snippet",
            "cmd": "search_run register_clipboard",
            "i3_shortcut": Shortcuts.SUPER_R,
            "gnome_shortcut": "<Super>r",
        },
        "register snippet search run": {
            "description": "Register to search run a string snippet",
            "cmd": "search_run register_snippet_clipboard",
            "i3_shortcut": Shortcuts.SUPER_SHIFT_R,
            "gnome_shortcut": "<Super><Shift>r",
        },
        "generate shortcuts python search": {
            "cmd": "search_run generate_shortcuts",
            "call_after": "restart i3",
            "i3_shortcut": Shortcuts.ALT_SHIFT_R,
            "gnome_shortcut": "<Alt><Shift>r",
        },
    }
