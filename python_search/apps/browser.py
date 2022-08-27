from __future__ import annotations

from python_search.environment import is_mac


class SupportedBrowsers:
    CHROME = "chrome"
    FIREFOX = "firefox"


class Browser:
    """
    Abstracts the browser features cross-platform
    """

    # a tuple with the binary and the type
    _MAC_DEFAULT_BROWSER = (
        '/usr/bin/open -a "/Applications/Google Chrome.app"',
        SupportedBrowsers.CHROME,
    )
    _LINUX_DEFAULT_BROWSER = "google-chrome", SupportedBrowsers.CHROME

    def open(self, url: str, app_mode=False, incognito=False) -> None:
        """
        performs the open
        """
        params = locals()
        del params["self"]
        cmd_to_run = self.open_cmd(**params)
        print("Comand to run:", cmd_to_run)
        from python_search.interpreter.cmd import CmdInterpreter

        CmdInterpreter({"cmd": cmd_to_run}).interpret_default()

    def open_cmd(self, url: str, app_mode=False, incognito=False) -> str:
        """
        Returns the shell command to open the browser
        """

        if is_mac():
            browser, type = self._MAC_DEFAULT_BROWSER
        else:
            browser, type = self._LINUX_DEFAULT_BROWSER

        # @todo this not always work consider adding a a retry mechanism
        # if type == SupportedBrowsers.CHROME and app_mode:
        #    return f"/Applications/Google\ Chrome.app/Contents/MacOS/Google\ Chrome  --app='{url}'"

        cmd = f"{browser} '{url}'"

        if type == SupportedBrowsers.CHROME and incognito:
            cmd = f"/Applications/Google\ Chrome.app/Contents/MacOS/Google\ Chrome  --incognito '{url}'"

        return cmd


def main():
    import fire

    fire.Fire(Browser)


if __name__ == "__main__":
    main()
