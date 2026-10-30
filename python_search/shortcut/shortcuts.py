"""
Shortcuts are declared once per entry, in the Mac glyph notation, and translated for each platform.

    "open mail": {"url": "...", "shortcuts": ["⌥M", "⌘⇧M"]},
    "open search": {"cmd": "...", "shortcut": "⌥Space"},
    "open whatsapp": {"cmd": "...", "shortcut_mac": "⌥W", "shortcuts_linux": ["⌥W", "⌘⇧W"]},

`shortcut`/`shortcuts` apply on every platform; `shortcut_mac`/`shortcuts_mac` only on macOS and
`shortcut_linux`/`shortcuts_linux` only on Linux.

Modifiers are ⌘ (Command, Super on Linux), ⌥ (Option/Alt), ⌃ (Control) and ⇧ (Shift), followed by a
single key: a letter, a digit, punctuation, "Space", or ↩/⏎/⌤ for Return.

"capslock" on its own binds the Caps Lock key, "right_command" the right Command (Super) key and "right_alt"
the right Option (Alt) key. Linux desktops cannot bind any of these keys alone, so keyd remaps each to a combination (KEYD_REMAPS, see keyd.py) and
the matching accelerator is bound instead.
"""

from __future__ import annotations

from typing import List, Optional, Tuple

SHORTCUT_FIELDS = ("shortcut", "shortcuts")
MAC = "mac"
LINUX = "linux"
PLATFORM_SHORTCUT_FIELDS = {
    MAC: ("shortcut_mac", "shortcuts_mac"),
    LINUX: ("shortcut_linux", "shortcuts_linux"),
}
ALL_SHORTCUT_FIELDS = SHORTCUT_FIELDS + PLATFORM_SHORTCUT_FIELDS[MAC] + PLATFORM_SHORTCUT_FIELDS[LINUX]

CAPS_LOCK = "capslock"
# On Linux keyd turns Caps Lock into this combination, and the desktop binds the matching accelerator.
KEYD_CAPS_LOCK = "C-A-M-space"
CAPS_LOCK_LINUX_ACCELERATOR = "<Control><Alt><Super>space"

RIGHT_COMMAND = "rightcommand"
# On Linux keyd turns the right Command (Super) key into this combination.
KEYD_RIGHT_COMMAND = "C-A-M-r"
RIGHT_COMMAND_LINUX_ACCELERATOR = "<Control><Alt><Super>r"

RIGHT_ALT = "rightalt"
# On Linux keyd turns the right Option (Alt) key into this combination.
KEYD_RIGHT_ALT = "C-A-M-o"
RIGHT_ALT_LINUX_ACCELERATOR = "<Control><Alt><Super>o"

# Karabiner-only bindings that fire on a lone modifier key; Linux desktops cannot bind those.
MODIFIER_ONLY_SHORTCUTS = ("right_gui", "right_gui_shift")

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


def current_platform() -> str:
    from python_search.environment import is_mac

    return MAC if is_mac() else LINUX


def entry_shortcuts(content, platform: Optional[str] = None) -> List[str]:
    """
    Every shortcut an entry declares for `platform` (default: the current one): the shared
    `shortcut`/`shortcuts` fields plus that platform's `shortcut_<platform>`/`shortcuts_<platform>`.
    """
    if not isinstance(content, dict):
        return []
    if platform is None:
        platform = current_platform()
    if platform not in PLATFORM_SHORTCUT_FIELDS:
        raise ValueError(f"Unknown platform {platform!r}, expected one of {list(PLATFORM_SHORTCUT_FIELDS)}")

    result = []
    for field in SHORTCUT_FIELDS + PLATFORM_SHORTCUT_FIELDS[platform]:
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


def is_right_alt(shortcut: str) -> bool:
    return _normalize(shortcut) == RIGHT_ALT


def keyd_remap(shortcut: str) -> Optional[Tuple[str, str]]:
    """The (keyd key name, combination) keyd must map for this shortcut to work on Linux, if any."""
    if is_caps_lock(shortcut):
        return "capslock", KEYD_CAPS_LOCK
    if is_right_command(shortcut):
        return "rightmeta", KEYD_RIGHT_COMMAND
    if is_right_alt(shortcut):
        return "rightalt", KEYD_RIGHT_ALT
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
    if is_right_alt(shortcut):
        return RIGHT_ALT_LINUX_ACCELERATOR

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
