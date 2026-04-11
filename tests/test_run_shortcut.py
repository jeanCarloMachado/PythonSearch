from unittest.mock import MagicMock

import pytest

from python_search.shortcut.runner import ShortcutRunner
from tests.utils import build_config


def test_run_shortcut_uses_matching_mac_shortcut():
    configuration = build_config(
        {
            "open mail": {"mac_shortcuts": ["⌥M", "⌘⇧M"]},
            "open search": {"mac_shortcut": "⌥Space"},
        }
    )
    runner = ShortcutRunner(configuration=configuration)
    runner._entry_runner = MagicMock()

    runner.run("⌥Space")

    runner._entry_runner.run.assert_called_once_with("open search", from_shortcut=True)


def test_run_shortcut_matches_case_and_whitespace_insensitively():
    configuration = build_config(
        {
            "open reports": {"gnome_shortcut": "Control+Shift+R"},
        }
    )
    runner = ShortcutRunner(configuration=configuration)
    runner._entry_runner = MagicMock()

    runner.run("control + shift + r")

    runner._entry_runner.run.assert_called_once_with("open reports", from_shortcut=True)


def test_run_shortcut_raises_when_pattern_is_not_configured():
    configuration = build_config(
        {
            "open search": {"mac_shortcut": "⌥Space"},
        }
    )
    runner = ShortcutRunner(configuration=configuration)

    with pytest.raises(Exception, match="No key found for shortcut pattern: ⌥R"):
        runner.run("⌥R")
