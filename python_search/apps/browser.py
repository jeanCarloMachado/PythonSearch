from __future__ import annotations
from python_search.environment import is_mac, is_linux
from typing import Optional, Literal
import os


class Browser:
    """
    Abstracts the browser features cross-platform
    """

    BROWSERS = Literal["firefox", "chrome"]

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
        params = locals()
        del params["self"]
        cmd_to_run = self.open_shell_cmd(**params)
        print("Command to run:", cmd_to_run)

        os.system(cmd_to_run)

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

        url_expr = ""
        if url is not None:
            url_expr = f"'{url}'"

        if browser == "chrome":
            return self._chrome(url_expr)

        if browser == "firefox":
            return self._firefox(url_expr)

        return self._chrome(url_expr)

    def _firefox(self, url):
        if is_mac():
            return f"open -a Firefox {url}"

        return f"firefox {url}"

    def _chrome(self, url: str):
        if is_mac():
            return f" open -a 'Google Chrome' {url}"

        if is_linux():
            local_browser = os.environ["BROWSER"]
            return f"{local_browser} {url}"


def main():
    import fire

    fire.Fire(Browser)


if __name__ == "__main__":
    main()
