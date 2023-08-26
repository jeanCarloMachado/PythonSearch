import unittest
from python_search.apps.browser import Browser
class TestBrowser(unittest.TestCase):
    def test_open_chrome_on_mac(self):
        def mock_system(cmd):
            self.assertEqual(cmd, "open -a 'Google Chrome' 'http://example.com'")

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

    def test_open_firefox_on_linux(self):
        def mock_system(cmd):
            self.assertEqual(cmd, "firefox 'http://example.com'")

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
