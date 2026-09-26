import pytest

from python_search.shortcut.shortcuts import entry_shortcuts, keyd_remap, to_linux_accelerator


def test_entry_shortcuts_reads_both_fields():
    content = {"shortcut": "⌥C", "shortcuts": ["⌘⇧M", "⌥M"]}

    assert entry_shortcuts(content) == ["⌥C", "⌘⇧M", "⌥M"]


def test_entry_shortcuts_ignores_non_dict_entries():
    assert entry_shortcuts("https://example.com") == []


@pytest.mark.parametrize(
    "shortcut, accelerator",
    [
        ("⌘⇧T", "<Shift><Super>t"),
        ("⇧⌘T", "<Shift><Super>t"),
        ("⌃⌥T", "<Control><Alt>t"),
        ("⌥Space", "<Alt>space"),
        ("⌘9", "<Super>9"),
        ("⌘⇧.", "<Shift><Super>period"),
        ("⌘⇧⏎", "<Shift><Super>Return"),
        ("⌘↩", "<Super>Return"),
    ],
)
def test_to_linux_accelerator(shortcut, accelerator):
    assert to_linux_accelerator(shortcut) == accelerator


@pytest.mark.parametrize("shortcut", ["capslock", "caps_lock", "CapsLock"])
def test_caps_lock_is_bound_to_the_keyd_combination(shortcut):
    assert to_linux_accelerator(shortcut) == "<Control><Alt><Super>space"


@pytest.mark.parametrize("shortcut", ["right_command", "Right_Command", "rightcommand"])
def test_right_command_is_bound_to_the_keyd_combination(shortcut):
    assert to_linux_accelerator(shortcut) == "<Control><Alt><Super>r"
    assert keyd_remap(shortcut) == ("rightmeta", "C-A-M-r")


def test_keyd_remap_is_none_for_regular_shortcuts():
    assert keyd_remap("⌘⇧T") is None


@pytest.mark.parametrize("shortcut", ["right_gui", "right_gui_shift", "right_alt", "⌘⇧"])
def test_to_linux_accelerator_skips_unbindable(shortcut):
    assert to_linux_accelerator(shortcut) is None
