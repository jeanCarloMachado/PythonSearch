from unittest.mock import MagicMock

import pytest

from python_search.shortcut.runner import ShortcutRunner
from tests.utils import build_config


def test_run_shortcut_uses_matching_shortcut():
    configuration = build_config(
        {
            "open mail": {"shortcuts": ["⌥M", "⌘⇧M"]},
            "open search": {"shortcut": "⌥Space"},
        }
    )
    runner = ShortcutRunner(configuration=configuration)
    runner._entry_runner = MagicMock()

    runner.run("⌥Space")

    runner._entry_runner.run.assert_called_once_with("open search", from_shortcut=True)


def test_run_shortcut_matches_case_and_whitespace_insensitively():
    configuration = build_config(
        {
            "open reports": {"shortcut": "⌘⇧R"},
        }
    )
    runner = ShortcutRunner(configuration=configuration)
    runner._entry_runner = MagicMock()

    runner.run("⌘ ⇧ r")

    runner._entry_runner.run.assert_called_once_with("open reports", from_shortcut=True)


def test_run_shortcut_raises_when_pattern_is_not_configured():
    configuration = build_config(
        {
            "open search": {"shortcut": "⌥Space"},
        }
    )
    runner = ShortcutRunner(configuration=configuration)

    with pytest.raises(Exception, match="No key found for shortcut pattern: ⌥R"):
        runner.run("⌥R")
