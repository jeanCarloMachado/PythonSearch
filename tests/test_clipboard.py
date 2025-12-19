import pytest
from unittest.mock import patch
from python_search.apps.clipboard import Clipboard


class TestClipboard:
    def test_set_and_get_content_roundtrip(self):
        """
        Test that content set via set_content can be retrieved via get_content.

        This validates the core business rule that the clipboard should preserve
        content between set and get operations. This is a happy path test that
        exercises the primary workflow end-to-end.

        The test works by mocking the subprocess calls to avoid actual clipboard
        interaction, while still testing the full logic flow including file I/O.

        This test can break easily if:
        - The temporary file path changes from /tmp/clipboard_content
        - The subprocess commands change (pbcopy/pbpaste vs xsel)
        - The chomp method logic is modified
        - Platform detection logic changes
        """
        clipboard = Clipboard()
        test_content = "Hello, World! This is a test string.\nWith multiple lines."

        # Mock platform detection and subprocess calls
        with patch("python_search.apps.clipboard.is_mac", return_value=True), patch(
            "subprocess.getoutput", return_value=test_content + "\n"
        ), patch("subprocess.Popen") as mock_popen, patch(
            "python_search.apps.notification_ui.send_notification"
        ):
            # Mock the Popen process for set_content
            mock_process = mock_popen.return_value.__enter__.return_value
            mock_process.communicate.return_value = (b"", None)
            mock_process.returncode = 0

            # Set content to clipboard
            clipboard.set_content(test_content, enable_notifications=False)

            # Get content back from clipboard
            retrieved_content = clipboard.get_content()

            # Assert the content matches (accounting for chomp behavior)
            assert retrieved_content == test_content

            # Verify the correct commands were used for Mac
            mock_popen.assert_called_once()
            call_args = mock_popen.call_args[0][0]
            assert "pbcopy" in call_args
            assert "/tmp/clipboard_content" in call_args

    def test_set_content_validation_errors(self):
        """
        Test that set_content properly validates input and raises exceptions.

        This validates the business rule that the clipboard should reject invalid
        inputs (empty content, non-string types) with clear error messages.
        This is a failure mode test that ensures proper error handling.

        The test works by calling set_content with various invalid inputs and
        verifying the expected exceptions are raised with correct messages.

        This test can break easily if:
        - The exception messages change
        - The validation logic is modified
        - New validation rules are added
        """
        clipboard = Clipboard()

        # Test empty content raises exception (mock stdin to avoid pytest issues)
        with patch("sys.stdin.readlines", return_value=[]):
            with pytest.raises(Exception, match="Tryring to set empty to clipboard"):
                clipboard.set_content("")

        with patch("sys.stdin.readlines", return_value=[]):
            with pytest.raises(Exception, match="Tryring to set empty to clipboard"):
                clipboard.set_content(None)

        # Test non-string content raises exception
        with pytest.raises(Exception, match="Tryring to set a non string to clipboard"):
            clipboard.set_content(123)

        with pytest.raises(Exception, match="Tryring to set a non string to clipboard"):
            clipboard.set_content(["list", "content"])

    def test_chomp_removes_trailing_characters(self):
        """
        Test that the chomp method correctly removes trailing newline characters.

        This validates the business rule that clipboard content should be cleaned
        of trailing whitespace/newlines for consistent behavior across platforms.
        This is a utility function test that ensures proper string processing.

        The test works by calling chomp with various string endings and verifying
        the correct characters are removed while preserving the main content.

        This test can break easily if:
        - The chomp logic changes (different characters to remove)
        - The order of character checking is modified
        - New character types are added to the removal list
        """
        clipboard = Clipboard()

        # Test different line ending scenarios
        assert clipboard.chomp("test\r\n") == "test"
        assert clipboard.chomp("test\n") == "test"
        assert clipboard.chomp("test\r") == "test"
        assert clipboard.chomp("test") == "test"
        assert (
            clipboard.chomp("test\r\n\r\n") == "test\r\n"
        )  # Only removes one occurrence
