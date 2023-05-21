from __future__ import annotations
from python_search.environment import is_mac, is_linux
from typing import Optional, Literal, Callable
import os


class Browser:
    """
    Abstracts the browser features cross-platform
    """

    BROWSERS = Literal["firefox", "chrome"]

    def __init__(
        self,
        system_func: Callable = os.system,
        is_mac_func: Callable = is_mac,
        is_linux_func: Callable = is_linux,
    ):
        self.system_func = system_func
        self.is_mac_func = is_mac_func
        self.is_linux_func = is_linux_func

    def open(
        self,
        url: Optional[str] = None,
        app_mode=False,
        incognito=False,
        browser: Optional[BROWSERS] = None,
    ) -> None:
        """
        performs the open
        """
        cmd_to_run = self.open_shell_cmd(url, app_mode, incognito, browser)
        print("Command to run:", cmd_to_run)
        self.system_func(cmd_to_run)

    def open_shell_cmd(
        self,
        url: Optional[str] = None,
        app_mode=False,
        incognito=False,
        browser: Optional[BROWSERS] = None,
    ) -> str:
        """
        Returns the shell command to open the browser
        """

        url_expr = f"'{url}'" if url else ""

        if browser == "chrome":
            return self._chrome(url_expr)

        if browser == "firefox":
            return self._firefox(url_expr)

        return self.fail_safe(url_expr)

    def _firefox(self, url: str):
        return "open -a Firefox {url}" if self.is_mac_func() else f"firefox {url}"

    def _chrome(self, url: str):
        return (
            f" open -a 'Google Chrome' {url}"
            if self.is_mac_func()
            else f"google-chrome {url}"
        )

    def fail_safe(self, url: str):
        if self.is_mac_func():
            return self._chrome(url)

        if self.is_linux_func():
            return self._firefox(url)

        raise Exception(
            "No supported browser found. Please install chrome/firefox or customize your browser in python_search/apps/browser.py"
        )


def main():
    import fire

    fire.Fire(Browser)


if __name__ == "__main__":
    main()
