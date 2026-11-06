import subprocess
import unittest
import unittest.mock

from python_search.host_system.windows_focus import Focus


class TestFocusMacChromeWindow(unittest.TestCase):
    def _focus(self, returncode=0, stdout="", stderr=""):
        result = subprocess.CompletedProcess([], returncode, stdout, stderr)
        with unittest.mock.patch(
            "python_search.host_system.windows_focus.is_mac", return_value=True
        ), unittest.mock.patch("subprocess.run", return_value=result):
            return Focus().focus_window("Google Chrome", "someone@example.com")

    def test_focused_window(self):
        self.assertTrue(self._focus(stdout="focused\n"))

    def test_no_matching_window(self):
        self.assertFalse(self._focus(stdout="not found\n"))

    def test_script_failure_raises_instead_of_reporting_no_window(self):
        with self.assertRaises(RuntimeError):
            self._focus(returncode=1, stderr="not authorized")


if __name__ == "__main__":
    unittest.main()
