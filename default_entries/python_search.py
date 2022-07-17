from python_search.config import PythonSearchConfiguration
from python_search.entries_group import EntriesGroup
from python_search.shortcuts import Shortcuts


class PythonSearch(EntriesGroup):
    """
    PythonSearch entries
    """

    commands = {
        "search run search focus or open": {
            "description": "Starts python search only once and reuse the same session",
            "focus_match": PythonSearchConfiguration.APPLICATION_TITLE,
            "cmd": "nice -19 python_search search",
            "i3_shortcut": "Mod1+space",
            "gnome_shortcut": "<Alt>space",
        },
        "save entry from clipboard inferring type": {
            "description": "Register to search run a string snippet",
            "cmd": "python_search register_clipboard",
            "i3_shortcut": Shortcuts.SUPER_R,
            "gnome_shortcut": "<Super>r",
        },
        "register snippet search run": {
            "description": "Register to search run a string snippet",
            "cmd": "python_search register_snippet_clipboard",
            "i3_shortcut": Shortcuts.SUPER_SHIFT_R,
            "gnome_shortcut": "<Super><Shift>r",
        },
        "generate shortcuts python search": {
            "cmd": "python_search generate_shortcuts",
            "call_after": "restart i3",
            "i3_shortcut": Shortcuts.ALT_SHIFT_R,
            "gnome_shortcut": "<Alt><Shift>r",
        },
    }
