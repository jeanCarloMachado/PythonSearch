"""Tests for CmdInterpreter, focused on the notify-on-failure/notify_output
behavior and the invariants it depends on:

- a plain "cmd" entry's wait-and-notify logic must live entirely inside the
  detached shell command, since run_key (the real caller) exits almost
  immediately and would kill any Python-side thread first.
- the wrapped command must isolate the original command in a subshell, not a
  `{ ...; }` group, so a bare `exit` inside it doesn't also skip the
  notify/cleanup steps.
- "cli_cmd" (terminal-wrapped) entries must be left untouched: their output
  lives in a separate Terminal window we never capture.
"""

from unittest.mock import MagicMock

import pytest

from python_search.exceptions import CommandDoNotMatchException
from python_search.interpreter.cmd import WRAP_IN_TERMINAL, CmdInterpreter


def test_string_cmd_is_wrapped_in_terminal():
    interp = CmdInterpreter("echo hello")

    assert interp.cmd[WRAP_IN_TERMINAL] is True
    assert interp.cmd["cmd"] == "echo hello"


def test_cli_cmd_dict_is_wrapped_in_terminal():
    interp = CmdInterpreter({"cli_cmd": "echo hello"})

    assert interp.cmd[WRAP_IN_TERMINAL] is True
    assert interp.cmd["cmd"] == "echo hello"


def test_plain_cmd_dict_is_not_wrapped_in_terminal():
    interp = CmdInterpreter({"cmd": "echo hello"})

    assert WRAP_IN_TERMINAL not in interp.cmd
    assert interp.cmd["cmd"] == "echo hello"


def test_invalid_dict_raises():
    with pytest.raises(CommandDoNotMatchException):
        CmdInterpreter({"url": "https://example.com"})


def test_wrap_with_notifications_uses_subshell_not_group():
    # A `{ ...; }` group would let a bare `exit` inside cmd terminate the
    # whole wrapper, skipping notify/cleanup. Must be a `( ... )` subshell.
    interp = CmdInterpreter({"cmd": "exit 1"})

    wrapped = interp._wrap_with_notifications("exit 1")

    assert "( exit 1 )" in wrapped
    assert "{ exit 1 ; }" not in wrapped


def test_wrap_with_notifications_default_does_not_notify_on_success():
    interp = CmdInterpreter({"cmd": "echo hi"})

    wrapped = interp._wrap_with_notifications("echo hi")

    # the success branch must be a no-op when notify_output is unset/False
    assert 'else true; fi' in wrapped


def test_wrap_with_notifications_with_notify_output_notifies_on_success(monkeypatch):
    monkeypatch.setattr(
        "python_search.interpreter.cmd.SystemPaths.get_binary_full_path",
        lambda name: f"/fake/bin/{name}",
    )
    interp = CmdInterpreter({"cmd": "echo hi", "notify_output": True})

    wrapped = interp._wrap_with_notifications("echo hi")

    assert "/fake/bin/notify_send" in wrapped
    assert '"$msg"' in wrapped
    assert "(no output)" in wrapped


def test_wrap_with_notifications_failure_branch_prefixes_entry_failed(monkeypatch):
    monkeypatch.setattr(
        "python_search.interpreter.cmd.SystemPaths.get_binary_full_path",
        lambda name: f"/fake/bin/{name}",
    )
    interp = CmdInterpreter({"cmd": "false"})

    wrapped = interp._wrap_with_notifications("false")

    assert '"Entry Failed: $msg"' in wrapped
    assert 'exit code $__rc' in wrapped


def test_wrap_with_notifications_cleans_up_temp_file(monkeypatch):
    monkeypatch.setattr(
        "python_search.interpreter.cmd.tempfile.mktemp",
        lambda suffix=".log": "/tmp/fixed_path.log",
    )
    interp = CmdInterpreter({"cmd": "echo hi"})

    wrapped = interp._wrap_with_notifications("echo hi")

    assert wrapped.strip().endswith("rm -f /tmp/fixed_path.log")
    assert wrapped.count("/tmp/fixed_path.log") >= 2


def test_execute_wraps_plain_cmd_with_notifications(monkeypatch):
    popen = MagicMock(return_value=MagicMock(pid=123))
    monkeypatch.setattr("python_search.interpreter.cmd.subprocess.Popen", popen)

    interp = CmdInterpreter({"cmd": "echo hi"})
    result = interp._execute("echo hi")

    assert result == {"pid": 123}
    executed_cmd = popen.call_args[0][0]
    assert executed_cmd != "echo hi"  # got wrapped
    assert "( echo hi )" in executed_cmd
    assert popen.call_args.kwargs["shell"] is True
    assert popen.call_args.kwargs["start_new_session"] is True


def test_execute_leaves_terminal_wrapped_cmd_untouched(monkeypatch):
    popen = MagicMock(return_value=MagicMock(pid=456))
    monkeypatch.setattr("python_search.interpreter.cmd.subprocess.Popen", popen)

    interp = CmdInterpreter({"cli_cmd": "echo hi"})
    result = interp._execute("echo hi")

    assert result == {"pid": 456}
    executed_cmd = popen.call_args[0][0]
    assert executed_cmd == "echo hi"  # not wrapped, no notification logic


def test_execute_never_uses_pipe_for_stdio(monkeypatch):
    # Regression guard: subprocess.PIPE ties the child's stdout to this
    # process's fd table, which breaks a longer-running detached child once
    # run_key exits (SIGPIPE on its next write). stdio must stay inherited.
    popen = MagicMock(return_value=MagicMock(pid=1))
    monkeypatch.setattr("python_search.interpreter.cmd.subprocess.Popen", popen)

    CmdInterpreter({"cmd": "echo hi"})._execute("echo hi")

    import subprocess as sp

    assert popen.call_args.kwargs["stdout"] is not sp.PIPE
    assert popen.call_args.kwargs["stderr"] is not sp.PIPE


def test_return_result_notifies_when_notify_result_key_present(monkeypatch):
    send_notification = MagicMock()
    monkeypatch.setattr(
        "python_search.interpreter.cmd.send_notification", send_notification
    )
    interp = CmdInterpreter({"cmd": "echo hi", "notify-result": True})

    result = interp.return_result({"pid": 1})

    send_notification.assert_called_once_with({"pid": 1})
    assert result == {"pid": 1}


def test_return_result_silent_without_notify_result_key(monkeypatch):
    send_notification = MagicMock()
    monkeypatch.setattr(
        "python_search.interpreter.cmd.send_notification", send_notification
    )
    interp = CmdInterpreter({"cmd": "echo hi"})

    interp.return_result({"pid": 1})

    send_notification.assert_not_called()


def test_copiable_part_returns_cmd_string():
    interp = CmdInterpreter({"cmd": "echo hi"})

    assert interp.copiable_part() == "echo hi"
