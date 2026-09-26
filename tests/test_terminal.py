import os
import shlex

from python_search.apps.iterm_terminal import ITermTerminal
from python_search.apps.terminal import KittyTerminal, terminal_for
from python_search.apps.terminator_terminal import TerminatorTerminal


def test_iterm_default_falls_back_to_terminator_off_mac():
    assert isinstance(terminal_for("iterm", on_mac=False), TerminatorTerminal)


def test_iterm_stays_on_mac():
    assert isinstance(terminal_for("iterm", on_mac=True), ITermTerminal)


def test_explicit_terminal_choices():
    assert isinstance(terminal_for("terminator", on_mac=True), TerminatorTerminal)
    assert isinstance(terminal_for("kitty", on_mac=False), KittyTerminal)


def test_terminator_runs_the_command_from_a_script():
    cmd = TerminatorTerminal().wrap_cmd_into_terminal("htop", title="htop mac")

    args = shlex.split(cmd)
    assert args[:5] == ["terminator", "--new-tab", "--geometry=1400x900", "--title", "htop mac"]
    assert args[5:8] == ["-x", "bash", "-i"]
    script = args[8]
    try:
        content = open(script).read()
        assert "\nhtop\n" in content
        assert "read\n" in content
    finally:
        os.remove(script)


def test_terminator_can_close_when_the_command_ends():
    cmd = TerminatorTerminal().wrap_cmd_into_terminal("ls", hold_terminal_open_on_end=False)

    script = shlex.split(cmd)[-1]
    try:
        assert "read\n" not in open(script).read()
    finally:
        os.remove(script)
