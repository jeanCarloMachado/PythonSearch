""" Test that all main apis are not breaking """
import os

binary = "search_run"


def test_all():
    assert_command_does_not_fail(f"{binary} --help")
    assert_command_does_not_fail(f"{binary} ranking --help")
    assert_command_does_not_fail(f"{binary} export_configuration --help")


def assert_command_does_not_fail(cmd):
    assert os.system(cmd) == 0
