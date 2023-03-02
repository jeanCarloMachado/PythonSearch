from __future__ import annotations
from python_search.environment import is_mac, is_linux
from typing import Optional, Literal
import os


class Browser:
    """
    Abstracts the browser features cross-platform
    """

    BROWSERS = Literal["firefox", "chrome"]

    def open(self, url: Optional[str] = None, app_mode=False, incognito=False) -> None:
        """
        performs the open
        """
        params = locals()
        del params["self"]
        cmd_to_run = self.open_shell_cmd(**params)
        print("Command to run:", cmd_to_run)

        import os

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
        local_browser = os.environ["BROWSER"]
        url_expr = ""
        if url is not None:
            url_expr = f"'{url}'"

        if is_linux():
            return f"{local_browser} {url_expr}"

        if incognito:
            return f'open -a "Google Chrome" --args -n --incognito "{url_expr}"'

        if is_mac():
            return f" open -a 'Google Chrome' {url_expr}"

        #return f"firefox {url_expr}"


def main():
    import fire

    fire.Fire(Browser)


if __name__ == "__main__":
    main()
