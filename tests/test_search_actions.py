from unittest.mock import patch, MagicMock
import pytest

from python_search.search.search_ui.search_actions import Actions


class TestActions:
    """Tests for the Actions class to ensure commands use binaries instead of python -m."""

    @patch("python_search.search.search_ui.search_actions.Popen")
    def test_copy_entry_value_to_clipboard_uses_binary_not_python_module(self, mock_popen):
        """
        Validates that copy_entry_value_to_clipboard uses the share_entry binary.

        This test ensures that clipboard copying uses the installed binary command
        rather than 'python -m python_search.share_entry', which is the project's
        preferred approach for CLI interactions.

        Business rule: All CLI commands should use installed binaries when available
        to ensure proper environment configuration and faster execution.

        How it works: Mocks Popen to capture the command being executed and verifies
        it uses the binary path from SystemPaths, not 'python -m'.

        This test can break if:
        - The command construction in copy_entry_value_to_clipboard changes
        - SystemPaths.get_binary_full_path behavior changes
        - Someone accidentally reverts to using 'python -m' pattern
        """
        # Setup
        actions = Actions()
        test_key = "test_entry_key"

        # Perform
        actions.copy_entry_value_to_clipboard(test_key)

        # Assert
        mock_popen.assert_called_once()
        command = mock_popen.call_args[0][0]

        # Verify binary is used, not python -m
        assert "python -m" not in command, f"Command should use binary, not 'python -m'. Got: {command}"
        assert "share_entry" in command, f"Command should include 'share_entry' binary. Got: {command}"
        assert "share_only_value" in command, f"Command should call 'share_only_value' method. Got: {command}"
        assert test_key in command, f"Command should include the entry key. Got: {command}"

    @patch("python_search.search.search_ui.search_actions.Popen")
    def test_run_key_uses_binary(self, mock_popen):
        """
        Validates that run_key uses the run_key binary.

        Business rule: Entry execution should use the installed run_key binary
        for consistent behavior and proper environment setup.

        This test can break if:
        - The command construction in run_key changes
        - Someone changes to use 'python -m' pattern
        """
        # Setup
        actions = Actions()
        test_key = "test_entry"

        # Perform
        actions.run_key(test_key)

        # Assert
        mock_popen.assert_called_once()
        command = mock_popen.call_args[0][0]

        assert "python -m" not in command, f"Command should use binary, not 'python -m'. Got: {command}"
        assert "run_key" in command, f"Command should include 'run_key' binary. Got: {command}"
        assert test_key in command, f"Command should include the entry key. Got: {command}"

    @patch("python_search.search.search_ui.search_actions.Popen")
    def test_search_in_google_uses_binaries(self, mock_popen):
        """
        Validates that search_in_google uses clipboard and run_key binaries.

        Business rule: Google search should use installed binaries for clipboard
        and run_key operations.

        This test can break if:
        - The command construction in search_in_google changes
        - Someone changes to use 'python -m' pattern
        """
        # Setup
        actions = Actions()
        test_query = "test search query"

        # Perform
        actions.search_in_google(test_query)

        # Assert
        mock_popen.assert_called_once()
        command = mock_popen.call_args[0][0]

        assert "python -m" not in command, f"Command should use binaries, not 'python -m'. Got: {command}"
        assert "clipboard" in command, f"Command should include 'clipboard' binary. Got: {command}"
        assert "run_key" in command, f"Command should include 'run_key' binary. Got: {command}"
        assert test_query in command, f"Command should include the search query. Got: {command}"

    @patch("python_search.search.search_ui.search_actions.Popen")
    def test_copy_entry_value_handles_special_characters_in_key(self, mock_popen):
        """
        Validates that copy_entry_value_to_clipboard properly quotes keys with special chars.

        Business rule: Entry keys may contain spaces or special characters and
        should be properly quoted in shell commands.

        This test can break if:
        - Quote handling in command construction changes
        - Key escaping logic is modified
        """
        # Setup
        actions = Actions()
        test_key = "entry with spaces"

        # Perform
        actions.copy_entry_value_to_clipboard(test_key)

        # Assert
        mock_popen.assert_called_once()
        command = mock_popen.call_args[0][0]

        # Key should be quoted
        assert f'"{test_key}"' in command, f"Key with spaces should be quoted. Got: {command}"
