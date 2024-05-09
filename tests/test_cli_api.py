""" Test that all main apis are not breaking """

import os

import pytest

binary = "python_search"


@pytest.mark.skipif("CI" in os.environ, reason="not supported on ci yet")
def test_all():
    assert_command_does_not_fail(f"{binary} --help")
    assert_command_does_not_fail(f"{binary} configure_shortcuts --help")
    assert_command_does_not_fail(f"{binary} install_missing_dependencies --help")
    assert_command_does_not_fail(f"{binary} new_project --help")
    assert_command_does_not_fail(f"{binary} set_project_location --help")
    assert_command_does_not_fail(f"{binary} register_new_ui --help")
    assert_command_does_not_fail(f"{binary} edit_entries_main --help")


def assert_command_does_not_fail(cmd):
    assert os.system(cmd) == 0
