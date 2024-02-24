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
        cmd_to_run = self.open_shell_cmd(
            url, app_mode, incognito, browser, focus_title=focus_title
        )
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

    def _firefox(self, url: str):
        return "open -a Firefox {url}" if self._is_mac() else f"firefox {url}"

    def _chrome(self, url: str):
        if self._is_mac():
            if self._focus_title or self._app_mode:
                send_notification(f"Open new chrome in app mode, can be a bit slow")

                return f"/Applications/Google\ Chrome.app/Contents/MacOS/Google\ Chrome --app={url}"

            return f"open -a 'Google Chrome' {url}"

        return f"google-chrome {url}"

    def fail_safe(self, url: str):
        if self._is_mac():
            return self._chrome(url)

        if self._is_linux():
            return self._firefox(url)

        raise Exception(
            "No supported browser found. Please install chrome/firefox or customize your browser in python_search/apps/browser.py"
        )


def main():
    import fire

    fire.Fire(Browser)


if __name__ == "__main__":
    main()
