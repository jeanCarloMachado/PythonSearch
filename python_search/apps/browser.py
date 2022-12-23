from __future__ import annotations

from typing import Optional, Literal


class Browser:
    """
    Abstracts the browser features cross-platform
    """

    BROSERS = Literal["firefox", "chrome"]

    def open(self, url: Optional[str] = None, app_mode=False, incognito=False) -> None:
        """
        performs the open
        """
        params = locals()
        del params["self"]
        cmd_to_run = self.open_shell_cmd(**params)
        print("Comand to run:", cmd_to_run)

        import os

        os.system(cmd_to_run)

    def open_shell_cmd(
        self,
        url: Optional[str] = None,
        app_mode=False,
        incognito=False,
        browser: Optional[BROSERS] = None,
    ) -> str:
        """
        Returns the shell command to open the browser
        """
        url_expr = ""
        if url is not None:
            url_expr = f"'{url}'"

        if browser == "chrome":
            cmd = f" open -a 'Google Chrome' {url_expr}"
        else:
            cmd = f" open -a Firefox {url_expr}"

        return cmd


def main():
    import fire

    fire.Fire(Browser)


if __name__ == "__main__":
    main()
