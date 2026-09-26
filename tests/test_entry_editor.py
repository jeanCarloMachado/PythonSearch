import os
import shutil
import subprocess
import sys

from python_search.entry_capture.entries_editor import EntriesEditor


def test_ripgrep_available():
    """Test that ripgrep is available (required search tool)"""
    has_ripgrep = shutil.which("rg") is not None
    assert (
        has_ripgrep
    ), "ripgrep (rg) is required for file searching. Install with: brew install ripgrep"


def test_ripgrep_functionality():
    """Test ripgrep basic functionality"""
    assert os.system("rg --help > /dev/null") == 0


def test_entries_editor_initialization():
    """Test that EntriesEditor uses the ripgrep found on PATH"""
    editor = EntriesEditor()
    assert editor._search_cmd == shutil.which("rg")


def test_entries_editor_search_command():
    """Test that EntriesEditor searches for the key as a dict key"""
    editor = EntriesEditor()
    cmd = editor._build_search_command("test_key")
    assert cmd[:6] == [shutil.which("rg"), "-n", "-i", "--type", "py", "--sort"]
    assert cmd[7] == "^\\s*[\"']test_key[\"']\\s*:"


def test_entries_editor_finds_key_declaration_not_other_mentions(tmp_path):
    """The key's own declaration is found, not a line that merely mentions it"""
    (tmp_path / "a_usage.py").write_text('if tab == "calendar":\n    x = "google calendar"\n')
    (tmp_path / "b_entries.py").write_text('entries = {\n    "google calendar": {\n        "url": "x",\n    },\n}\n')
    editor = EntriesEditor()
    editor.configuration.get_project_root = lambda: str(tmp_path)

    out = subprocess.run(
        editor._build_search_command("google calendar"), capture_output=True, text=True
    ).stdout

    assert out.splitlines()[0] == f"{tmp_path}/b_entries.py:2:    \"google calendar\": {{"


def test_entries_editor_edit_key_help_command_returns_output():
    """
    Validates that the entries_editor edit_key -h shell command returns
    meaningful help output.

    Business rule: The CLI must provide help documentation for the edit_key
    command to assist users.
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
        sys.executable,
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
        cwd=os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
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
    assert "SYNOPSIS" in help_output, (
        f"Help output should contain standard Fire help sections. "
        f"Got: {help_output}"
    )

    # Ensure output is not empty
    assert len(help_output.strip()) > 50, (
        f"Help output should be substantial, not just a brief message. "
        f"Got: {help_output}"
    )
