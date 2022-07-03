""" Test that all main apis are not breaking """
import os

import pytest

binary = "search_run"


@pytest.mark.skipif("CI" in os.environ, reason="not supported on ci yet")
def test_all():
    assert_command_does_not_fail(f"{binary} --help")
    assert_command_does_not_fail(f"{binary} ranking --help")
    assert_command_does_not_fail(f"{binary} generate_shortcuts --help")
    assert_command_does_not_fail(f"{binary} consumers --help")
    assert_command_does_not_fail(f"{binary} consumers latest_used_entries --help")


def assert_command_does_not_fail(cmd):
    assert os.system(cmd) == 0
