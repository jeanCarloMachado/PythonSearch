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
        "/Applications/Google\ Chrome.app/Contents/MacOS/Google\ Chrome ",
        SupportedBrowsers.CHROME,
    )
    _LINUX_DEFAULT_BROWSER = "google-chrome", SupportedBrowsers.CHROME

    def open(self, url: str, app_mode=False, incognito=False) -> None:
        """
        performs the open
        """
        params = locals()
        del params["self"]
        cmd_to_run = self.open_shell_cmd(**params)
        print("Comand to run:", cmd_to_run)

        import os

        os.system(cmd_to_run)

    def open_shell_cmd(self, url: str, app_mode=False, incognito=False) -> str:
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

        # open -a is much faster on mac to open url
        # i suppose it is so because it does not have to do chrome startup again
        # while calling the binary directly does
        # cmd = f"/usr/bin/open -a '/Applications/Google Chrome.app' '{url}'"
        # cmd = f'open -b com.google.chrome "{url}"'
        # this is too slow
        # cmd = f'/Applications/Google\ Chrome.app/Contents/MacOS/Google\ Chrome "{url}"'
        # this does not work always
        cmd = f'open -g "{url}" '

        return cmd


def main():
    import fire

    fire.Fire(Browser)


if __name__ == "__main__":
    main()
