import unittest
from unittest.mock import MagicMock

import pytest

from python_search.interpreter.cmd import CmdInterpreter
from python_search.interpreter.url import UrlInterpreter


class TestUrlCase(unittest.TestCase):
    def test_create(self):
        """Test that initializing with str url does not throw exception"""
        UrlInterpreter("http://www.google.com")
        assert True

    def test_create_fails(self):
        """Test that initializing with str url does not throw exception"""
        self.assertRaises(Exception, UrlInterpreter, "not a url")


def test_default_does_not_require_run_before_cmd(monkeypatch):
    monkeypatch.setattr(
        "python_search.interpreter.url.Browser.open_shell_cmd",
        lambda self, url, browser=None, focus_title=None: f"open {url}",
    )
    monkeypatch.setattr(
        CmdInterpreter,
        "interpret_default",
        lambda self: self.cmd["cmd"],
    )
    context = MagicMock()

    result = UrlInterpreter({"url": "https://example.com"}, context=context).default()

    assert result == "open https://example.com"


def test_default_runs_run_before_cmd_once(monkeypatch):
    calls = []

    monkeypatch.setattr(
        "python_search.interpreter.url.Browser.open_shell_cmd",
        lambda self, url, browser=None, focus_title=None: f"open {url}",
    )
    monkeypatch.setattr(
        CmdInterpreter,
        "interpret_default",
        lambda self: self.cmd["cmd"],
    )

    def fake_run_before(self, cmd):
        calls.append(cmd)

    monkeypatch.setattr(UrlInterpreter, "run_shell_pre_command", fake_run_before)
    context = MagicMock()

    UrlInterpreter(
        {"url": "https://example.com", "run_before_cmd": "echo setup"},
        context=context,
    ).default()

    assert calls == ["echo setup"]


def test_default_ignores_none_run_before_cmd(monkeypatch):
    monkeypatch.setattr(
        "python_search.interpreter.url.Browser.open_shell_cmd",
        lambda self, url, browser=None, focus_title=None: f"open {url}",
    )
    monkeypatch.setattr(
        CmdInterpreter,
        "interpret_default",
        lambda self: self.cmd["cmd"],
    )
    context = MagicMock()

    result = UrlInterpreter(
        {"url": "https://example.com", "run_before_cmd": None},
        context=context,
    ).default()

    assert result == "open https://example.com"


def test_default_ignores_empty_run_before_cmd(monkeypatch):
    monkeypatch.setattr(
        "python_search.interpreter.url.Browser.open_shell_cmd",
        lambda self, url, browser=None, focus_title=None: f"open {url}",
    )
    monkeypatch.setattr(
        CmdInterpreter,
        "interpret_default",
        lambda self: self.cmd["cmd"],
    )
    context = MagicMock()

    result = UrlInterpreter(
        {"url": "https://example.com", "run_before_cmd": ""},
        context=context,
    ).default()

    assert result == "open https://example.com"
