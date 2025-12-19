import subprocess
from unittest.mock import patch, MagicMock
import pytest

from python_search.share_entry import ShareEntry


class TestShareEntry:
    """Tests for the ShareEntry functionality to ensure it's properly installed."""

    def test_share_entry_module_can_be_imported_and_executed_via_python_module(
        self,
    ):
        """
        Validates that share_entry can be found and executed as a Python module.

        This test ensures that the share_entry functionality is properly installed
        and accessible via 'python -m python_search.share_entry' command, which is
        critical for the search UI clipboard functionality to work.

        Business rule: The share_entry module must be executable as a Python module
        to support copying entry values to clipboard from the terminal UI.

        How it works: Executes the module with --help flag to verify it's accessible
        and then tests the specific share_only_value method that's used by the UI.

        This test can break if:
        - The share_entry.py module is missing or has import errors
        - The module's main() function or fire.Fire() setup is broken
        - Python path or module structure changes
        - The share_only_value method is renamed or removed
        """
        # Setup: Prepare commands to test module accessibility
        base_command = ["python", "-m", "python_search.share_entry", "--help"]
        method_command = [
            "python",
            "-m",
            "python_search.share_entry",
            "share_only_value",
            "--help",
        ]

        # Perform: Execute the module commands
        base_result = subprocess.run(
            base_command, capture_output=True, text=True, timeout=10
        )
        method_result = subprocess.run(
            method_command, capture_output=True, text=True, timeout=10
        )

        # Assert: Module should be accessible and show help output
        assert (
            base_result.returncode == 0
        ), f"Module execution failed: {base_result.stderr}"
        assert (
            method_result.returncode == 0
        ), f"Method execution failed: {method_result.stderr}"

        base_output = base_result.stdout + base_result.stderr
        method_output = method_result.stdout + method_result.stderr

        assert "share_entry.py" in base_output, "Expected module name not found in help"
        assert (
            "share_only_value" in method_output
        ), "Expected share_only_value method not accessible"
        assert "KEY" in method_output, "Expected KEY parameter not found in method help"

    @patch("python_search.share_entry.Clipboard")
    @patch("python_search.share_entry.ConfigurationLoader")
    def test_share_only_value_copies_entry_content_to_clipboard(
        self, mock_loader, mock_clipboard
    ):
        """
        Validates that share_only_value correctly extracts and copies entry content.

        This test ensures the core business logic of copying entry values works,
        which is essential for the terminal UI's copy-to-clipboard feature.

        Business rule: When copying an entry value, only the content should
        be copied to clipboard, and the user should be notified of the action.

        How it works: Mocks the configuration loader and clipboard, then verifies that
        the correct entry content is extracted and copied with notifications.

        This test can break if:
        - Entry content extraction logic changes
        - Clipboard interface or notification parameters change
        - Key resolution from fzf format fails
        - Entry lookup or validation logic is modified
        """
        # Setup: Create mock entry data and dependencies
        mock_entries = {
            "test_key": {"snippet": "test content value", "type": "snippet"}
        }
        mock_loader.return_value.load_entries.return_value = mock_entries
        mock_clipboard_instance = MagicMock()
        mock_clipboard.return_value = mock_clipboard_instance

        share_entry = ShareEntry()

        # Perform: Execute share_only_value with test key
        result = share_entry.share_only_value("test_key")

        # Assert: Verify correct content is copied with proper settings
        assert result == "test content value"
        mock_clipboard_instance.set_content.assert_called_once_with(
            "test content value", enable_notifications=True, notify=True
        )

    @patch("python_search.share_entry.ConfigurationLoader")
    def test_share_only_value_raises_exception_for_nonexistent_entry(self, mock_loader):
        """
        Validates that share_only_value properly handles missing entries.

        This test ensures robust error handling when users attempt to copy
        non-existent entries, preventing silent failures in the terminal UI.

        Business rule: Attempting to copy a non-existent entry should raise
        a clear exception rather than failing silently or causing crashes.

        How it works: Mocks an empty entries configuration and verifies that
        attempting to share a non-existent key raises an appropriate exception.

        This test can break if:
        - Exception handling logic is removed or changed
        - Entry existence validation is modified
        - Error message format changes
        - Key resolution logic changes behavior for missing keys
        """
        # Setup: Create empty entries configuration
        mock_loader.return_value.load_entries.return_value = {}
        share_entry = ShareEntry()

        # Perform & Assert: Verify exception is raised for missing entry
        with pytest.raises(Exception) as exc_info:
            share_entry.share_only_value("nonexistent_key")

        assert "Entry nonexistent_key not found" in str(exc_info.value)
