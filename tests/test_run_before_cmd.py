"""Tests for run_before_cmd on entries."""

from unittest.mock import MagicMock

import pytest

from python_search.interpreter.base import BaseInterpreter


class _RecordingInterpreter(BaseInterpreter):
    def interpret_default(self):
        self._main_ran = True
        return "ok"


def test_run_before_cmd_runs_before_main(monkeypatch):
    order = []

    def fake_run(cmd, **kwargs):
        order.append("before")
        return MagicMock(returncode=0)

    monkeypatch.setattr("python_search.interpreter.base.subprocess.run", fake_run)
    ctx = MagicMock()
    ctx.enable_sequential_execution = MagicMock()
    interp = _RecordingInterpreter(
        {"run_before_cmd": "echo setup", "cmd": "echo main"},
        context=ctx,
    )
    interp.default()
    assert order == ["before"]
    assert interp._main_ran is True


def test_run_before_cmd_failure_raises(monkeypatch):
    def fake_run(cmd, **kwargs):
        return MagicMock(returncode=1)

    monkeypatch.setattr("python_search.interpreter.base.subprocess.run", fake_run)
    ctx = MagicMock()
    ctx.enable_sequential_execution = MagicMock()
    interp = _RecordingInterpreter(
        {"run_before_cmd": "false", "cmd": "echo main"},
        context=ctx,
    )
    with pytest.raises(RuntimeError, match="run_before_cmd failed"):
        interp.default()
    assert not getattr(interp, "_main_ran", False)
