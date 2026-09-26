"""
Shortcuts are declared once per entry, in the Mac glyph notation, and translated for each platform.

    "open mail": {"url": "...", "shortcuts": ["⌥M", "⌘⇧M"]},
    "open search": {"cmd": "...", "shortcut": "⌥Space"},

Modifiers are ⌘ (Command, Super on Linux), ⌥ (Option/Alt), ⌃ (Control) and ⇧ (Shift), followed by a
single key: a letter, a digit, punctuation, "Space", or ↩/⏎/⌤ for Return.

"capslock" on its own binds the Caps Lock key, and "right_command" the right Command (Super) key. Linux
desktops cannot bind either key alone, so keyd remaps each to a combination (KEYD_REMAPS, see keyd.py) and
the matching accelerator is bound instead.
"""

from __future__ import annotations

from typing import List, Optional, Tuple

SHORTCUT_FIELDS = ("shortcut", "shortcuts")

CAPS_LOCK = "capslock"
# On Linux keyd turns Caps Lock into this combination, and the desktop binds the matching accelerator.
KEYD_CAPS_LOCK = "C-A-M-space"
CAPS_LOCK_LINUX_ACCELERATOR = "<Control><Alt><Super>space"

RIGHT_COMMAND = "rightcommand"
# On Linux keyd turns the right Command (Super) key into this combination.
KEYD_RIGHT_COMMAND = "C-A-M-r"
RIGHT_COMMAND_LINUX_ACCELERATOR = "<Control><Alt><Super>r"

# Karabiner-only bindings that fire on a lone modifier key; Linux desktops cannot bind those.
MODIFIER_ONLY_SHORTCUTS = ("right_gui", "right_gui_shift", "right_alt")

RETURN_GLYPHS = ("↩", "⏎", "⌤")

# Glyph → GTK accelerator modifier, in the order GNOME and XFCE write them.
LINUX_MODIFIERS = (
    ("⌃", "<Control>"),
    ("⌥", "<Alt>"),
    ("⇧", "<Shift>"),
    ("⌘", "<Super>"),
)

# Punctuation → X keysym name, which is what GTK accelerators expect.
LINUX_KEY_NAMES = {
    ".": "period",
    ",": "comma",
    "/": "slash",
    ";": "semicolon",
    "'": "apostrophe",
    "[": "bracketleft",
    "]": "bracketright",
    "-": "minus",
    "=": "equal",
    "`": "grave",
    "\\": "backslash",
}


def entry_shortcuts(content) -> List[str]:
    """Every shortcut declared on an entry, from both `shortcut` and `shortcuts`."""
    if not isinstance(content, dict):
        return []

    result = []
    for field in SHORTCUT_FIELDS:
        value = content.get(field)
        if value is None:
            continue
        if isinstance(value, (list, tuple)):
            result.extend(str(shortcut) for shortcut in value)
        else:
            result.append(str(value))
    return result


def _normalize(shortcut: str) -> str:
    return shortcut.replace("_", "").replace(" ", "").lower()


def is_caps_lock(shortcut: str) -> bool:
    return _normalize(shortcut) == CAPS_LOCK


def is_right_command(shortcut: str) -> bool:
    return _normalize(shortcut) == RIGHT_COMMAND


def keyd_remap(shortcut: str) -> Optional[Tuple[str, str]]:
    """The (keyd key name, combination) keyd must map for this shortcut to work on Linux, if any."""
    if is_caps_lock(shortcut):
        return "capslock", KEYD_CAPS_LOCK
    if is_right_command(shortcut):
        return "rightmeta", KEYD_RIGHT_COMMAND
    return None


def to_linux_accelerator(shortcut: str) -> Optional[str]:
    """
    Translate "⌘⇧T" into the GTK accelerator "<Shift><Super>t" used by GNOME and XFCE.

    Returns None for shortcuts Linux cannot bind: a lone modifier key, or modifiers with no key.
    """
    if shortcut in MODIFIER_ONLY_SHORTCUTS:
        return None
    if is_caps_lock(shortcut):
        return CAPS_LOCK_LINUX_ACCELERATOR
    if is_right_command(shortcut):
        return RIGHT_COMMAND_LINUX_ACCELERATOR

    remaining = shortcut.replace(" ", "")
    modifiers = ""
    for glyph, accelerator in LINUX_MODIFIERS:
        if glyph in remaining:
            modifiers += accelerator
            remaining = remaining.replace(glyph, "")

    if not remaining:
        return None
    if remaining in RETURN_GLYPHS:
        key = "Return"
    elif remaining.lower() == "space":
        key = "space"
    elif remaining in LINUX_KEY_NAMES:
        key = LINUX_KEY_NAMES[remaining]
    elif len(remaining) == 1 and remaining.isalnum():
        key = remaining.lower()
    else:
        return None

    return modifiers + key
