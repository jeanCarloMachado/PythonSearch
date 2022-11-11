""" Test that all main apis are not breaking """
import os

import pytest

binary = "python_search"


@pytest.mark.skipif("CI" in os.environ, reason="not supported on ci yet")
def test_all():
    assert_command_does_not_fail(f"{binary} --help")
    assert_command_does_not_fail(f"{binary} shortcut_generator generate --help")


def assert_command_does_not_fail(cmd):
    assert os.system(cmd) == 0
