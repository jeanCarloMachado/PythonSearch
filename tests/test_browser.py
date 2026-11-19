import unittest
import unittest.mock
from python_search.apps.browser import Browser


class TestBrowser(unittest.TestCase):
    def test_open_chrome_on_mac(self):
        def mock_system(cmd):
            self.assertEqual(
                cmd,
                Browser.MAC_CHROME_BINARY + " 'http://example.com' >/dev/null 2>&1 &",
            )

        def mock_is_mac():
            return True

        def mock_is_linux():
            return False

        b = Browser(
            system_func=mock_system,
            is_mac_func=mock_is_mac,
            is_linux_func=mock_is_linux,
        )
        b.open(url="http://example.com", browser="chrome")

    def test_default_is_chrome_binary_on_mac(self):
        b = Browser(system_func=None, is_mac_func=lambda: True, is_linux_func=lambda: False)
        cmd = b.open_shell_cmd(url="http://example.com")
        self.assertEqual(
            cmd, Browser.MAC_CHROME_BINARY + " 'http://example.com' >/dev/null 2>&1 &"
        )

    def test_mac_chrome_does_not_route_through_launch_services(self):
        """`open -a` can hand the URL to an automation Chrome (e.g. Playwright) and open
        it in the wrong profile; a --user-data-dir would pin a profile other than the user's."""
        b = Browser(system_func=None, is_mac_func=lambda: True, is_linux_func=lambda: False)
        cmd = b.open_shell_cmd(url="http://example.com", browser="chrome")
        self.assertNotIn("open -a", cmd)
        self.assertNotIn("--user-data-dir", cmd)

    def test_mac_chrome_runs_in_background(self):
        """If Chrome isn't running, the binary becomes the browser and would block os.system."""
        b = Browser(system_func=None, is_mac_func=lambda: True, is_linux_func=lambda: False)
        cmd = b.open_shell_cmd(url="http://example.com", browser="chrome")
        self.assertTrue(cmd.endswith(" &"))

    def test_app_mode_uses_chrome_binary_on_mac(self):
        b = Browser(system_func=None, is_mac_func=lambda: True, is_linux_func=lambda: False)
        with unittest.mock.patch("python_search.apps.browser.send_notification"):
            cmd = b.open_shell_cmd(url="http://example.com", app_mode=True, browser="chrome")
        self.assertEqual(cmd, Browser.MAC_CHROME_BINARY + " --app='http://example.com'")

    def test_mac_chrome_binary_path_is_shell_escaped(self):
        self.assertEqual(
            Browser.MAC_CHROME_BINARY,
            "/Applications/Google\\ Chrome.app/Contents/MacOS/Google\\ Chrome",
        )

    def test_open_firefox_on_linux(self):
        def mock_system(cmd):
            self.assertEqual(cmd, "firefox 'http://example.com'; " + Browser.LINUX_FOCUS_FIREFOX_CMD + " >/dev/null 2>&1")

        def mock_is_mac():
            return False

        def mock_is_linux():
            return True

        b = Browser(
            system_func=mock_system,
            is_mac_func=mock_is_mac,
            is_linux_func=mock_is_linux,
        )
        b.open(url="http://example.com", browser="firefox")

    def test_default_is_firefox_on_linux(self):
        b = Browser(
            system_func=None, is_mac_func=lambda: False, is_linux_func=lambda: True
        )
        with unittest.mock.patch(
            "shutil.which", side_effect=lambda name: f"/usr/bin/{name}"
        ):
            cmd = b.open_shell_cmd(url="http://example.com")
        self.assertEqual(cmd, "firefox 'http://example.com'; " + Browser.LINUX_FOCUS_FIREFOX_CMD + " >/dev/null 2>&1")

    def test_app_mode_is_chrome_on_linux(self):
        b = Browser(
            system_func=None, is_mac_func=lambda: False, is_linux_func=lambda: True
        )
        with unittest.mock.patch(
            "shutil.which",
            side_effect=lambda name: None if name == "google-chrome" else f"/usr/bin/{name}",
        ):
            cmd = b.open_shell_cmd(url="http://example.com", app_mode=True)
        self.assertEqual(cmd, "google-chrome-stable --app='http://example.com'")

    def test_default_falls_back_to_chrome_without_firefox_on_linux(self):
        b = Browser(
            system_func=None, is_mac_func=lambda: False, is_linux_func=lambda: True
        )
        with unittest.mock.patch(
            "shutil.which",
            side_effect=lambda name: "/usr/bin/google-chrome-stable"
            if name == "google-chrome-stable"
            else None,
        ):
            cmd = b.open_shell_cmd(url="http://example.com")
        self.assertEqual(cmd, "google-chrome-stable 'http://example.com'")

    def test_default_falls_back_to_firefox_without_chrome_on_linux(self):
        b = Browser(
            system_func=None, is_mac_func=lambda: False, is_linux_func=lambda: True
        )
        with unittest.mock.patch(
            "shutil.which",
            side_effect=lambda name: "/usr/bin/firefox" if name == "firefox" else None,
        ):
            cmd = b.open_shell_cmd(url="http://example.com")
        self.assertEqual(cmd, "firefox 'http://example.com'; " + Browser.LINUX_FOCUS_FIREFOX_CMD + " >/dev/null 2>&1")

    def test_fail_safe_no_supported_browser(self):
        def mock_is_mac():
            return False

        def mock_is_linux():
            return False

        b = Browser(
            system_func=None, is_mac_func=mock_is_mac, is_linux_func=mock_is_linux
        )
        with self.assertRaises(Exception) as context:
            b.open(url="http://example.com")
        self.assertTrue(
            "No supported browser found. Please install chrome/firefox or customize your browser in python_search/apps/browser.py"
            in str(context.exception)
        )


if __name__ == "__main__":
    unittest.main()
