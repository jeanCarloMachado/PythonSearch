from __future__ import annotations

import sys

from python_search.environment import is_mac, is_linux
from typing import Optional, Literal, Callable
import os
from python_search.apps.notification_ui import send_notification


class Browser:
    """
    Abstracts the browser features cross-platform
    """

    BROWSERS = Literal["firefox", "chrome"]
    _app_mode = False
    LINUX_FOCUS_FIREFOX_CMD = (
        "gdbus call --session --dest org.gnome.Shell --object-path /org/gnome/Shell/Extensions/WindowManager "
        "--method org.gnome.Shell.Extensions.WindowManager.FocusByWmClass firefox"
    )

    def __init__(
        self,
        system_func: Callable = os.system,
        is_mac_func: Callable = is_mac,
        is_linux_func: Callable = is_linux,
    ):
        self.system_func = system_func
        self._is_mac = is_mac_func
        self._is_linux = is_linux_func

    def open(
        self,
        url: Optional[str] = None,
        app_mode=False,
        incognito=False,
        browser: Optional[BROWSERS] = None,
        focus_title: Optional[str] = None,
    ) -> None:
        """
        performs the open

        focus_title: to focus on a window that behaves like an app
        """
        url = url.strip()
        cmd_to_run = self.open_shell_cmd(url, app_mode, incognito, browser, focus_title=focus_title)
        print("Command to run:", cmd_to_run)
        self.system_func(cmd_to_run)

    def open_shell_cmd(
        self,
        url: Optional[str] = None,
        app_mode=None,
        incognito=False,
        browser: Optional[BROWSERS] = None,
        focus_title=None,
    ) -> str:
        """
        Returns the shell command to open the browser
        """

        self._focus_title = focus_title
        self._app_mode = app_mode

        if self._focus_title:
            from python_search.host_system.windows_focus import Focus

            if Focus().focus_window("Google Chrome", self._focus_title):
                print("Chrome window focused instead of opening new")
                sys.exit(0)

        url_expr = f"'{url}'" if url else ""

        if browser == "chrome":
            return self._chrome(url_expr)

        if browser == "firefox":
            return self._firefox(url_expr)

        return self.fail_safe(url_expr)

    def open_stdin(self):
        import sys

        self.open(sys.stdin.read())

    def _firefox(self, url: str):
        if self._is_mac():
            return f"open -a Firefox {url}"
        # A tab opened in a running window doesn't take focus on GNOME Wayland, so ask the
        # window-manager@monorepo extension to focus it.
        return f"firefox {url}; {self.LINUX_FOCUS_FIREFOX_CMD} >/dev/null 2>&1"  # noqa: E702

    MAC_CHROME_BINARY = "/Applications/Google\\ Chrome.app/Contents/MacOS/Google\\ Chrome"

    def _chrome(self, url: str):
        if self._is_mac():
            profile = f"--profile-directory='{self._mac_chrome_last_used_profile()}'"
            if self._focus_title or self._app_mode:
                send_notification("Open new chrome in app mode, can be a bit slow")

                return f"{self.MAC_CHROME_BINARY} {profile} --app={url}"

            # Not `open -a 'Google Chrome'`: with an automation Chrome (e.g. Playwright) running
            # from the same bundle, LaunchServices can hand the URL to it and open it in its
            # throwaway profile. The binary without --user-data-dir always reaches the user's
            # Chrome; --profile-directory picks the profile that was focused last.
            # Backgrounded because it stays in the foreground if Chrome isn't running yet.
            return f"{self.MAC_CHROME_BINARY} {profile} {url} >/dev/null 2>&1 &"

        binary = self._linux_chrome_binary() or "google-chrome"
        if self._focus_title or self._app_mode:
            return f"{binary} --app={url}"
        return f"{binary} {url}"

    @staticmethod
    def _mac_chrome_profile_state() -> dict:
        import json

        local_state = os.path.expanduser("~/Library/Application Support/Google/Chrome/Local State")
        with open(local_state) as f:
            return json.load(f)["profile"]

    @classmethod
    def _mac_chrome_last_used_profile(cls) -> str:
        return cls._mac_chrome_profile_state()["last_used"]

    @classmethod
    def mac_chrome_last_used_profile_email(cls) -> str:
        """Email of the Chrome profile that was focused most recently."""
        state = cls._mac_chrome_profile_state()
        return state["info_cache"][state["last_used"]]["user_name"]

    @staticmethod
    def _linux_chrome_binary() -> Optional[str]:
        """Arch and some other distros only install `google-chrome-stable`."""
        import shutil

        for name in ("google-chrome", "google-chrome-stable"):
            if shutil.which(name):
                return name
        return None

    def fail_safe(self, url: str):
        """Chrome is the default on Mac. On Linux, Firefox opens new sessions and Chrome
        opens app mode (--app windows); each falls back to the other when missing."""
        import shutil

        if self._is_mac():
            return self._chrome(url)

        if self._is_linux():
            has_chrome = self._linux_chrome_binary() is not None
            if (self._app_mode or self._focus_title) and has_chrome:
                return self._chrome(url)
            if shutil.which("firefox") or not has_chrome:
                return self._firefox(url)
            return self._chrome(url)

        raise Exception(
            "No supported browser found. Please install chrome/firefox or customize your browser in python_search/apps/browser.py"  # noqa: E501
        )


def main():
    import fire

    fire.Fire(Browser)


if __name__ == "__main__":
    main()
