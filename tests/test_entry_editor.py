import os
import subprocess

from python_search.entry_capture.entries_editor import EntriesEditor


def test_ack():
    assert os.system(f"{EntriesEditor.ACK_PATH} --help") == 0


def test_entries_editor_edit_key_help_command_returns_output():
    """
    Validates that the entries_editor edit_key -h shell command returns meaningful help output.

    Business rule: The CLI must provide help documentation for the edit_key command to assist users.
    Purpose: Ensures the help system works correctly and returns expected content.

    How it works:
    1. Executes the entries_editor edit_key --help command via subprocess
    2. Validates the command succeeds (exit code 0)
    3. Checks that help output contains expected key information

    How this test can break easily:
    - If the Fire library integration is broken, the command will fail
    - If the edit_key method is renamed or removed, help won't be available
    - If the module path changes, the command won't be found
    - If Python path issues occur, the module won't be importable
    """
    # setup
    cmd = [
        "python",
        "-m",
        "python_search.entry_capture.entries_editor",
        "edit_key",
        "--help",
    ]

    # perform
    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        cwd="/Users/jean.machado@getyourguide.com/prj/PythonSearch",
    )

    # assert
    assert (
        result.returncode == 0
    ), f"Command failed with exit code {result.returncode}. stderr: {result.stderr}"

    # Fire library outputs help to stderr, not stdout
    help_output = result.stderr
    assert (
        "edit_key" in help_output
    ), f"Help output should mention the edit_key command. Got: {help_output}"
    assert (
        "KEY_EXPR" in help_output
    ), f"Help output should mention the KEY_EXPR parameter. Got: {help_output}"
    assert (
        "Edits the configuration files" in help_output
    ), f"Help output should contain the method docstring. Got: {help_output}"
    assert (
        "SYNOPSIS" in help_output
    ), f"Help output should contain standard Fire help sections. Got: {help_output}"

    # Ensure output is not empty
    assert (
        len(help_output.strip()) > 50
    ), f"Help output should be substantial, not just a brief message. Got: {help_output}"
