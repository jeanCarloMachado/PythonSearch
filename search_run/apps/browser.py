from search_run.interpreter.cmd import CmdEntry


class Browser:
    def open(self, url: str):
        """
        Opens a url in your browser
        if get_command_only is true returns the command to execute rather than executing it

        """

        import os

        cmd = f"{os.getenv('BROWSER')} {url}"
        CmdEntry({"cmd": cmd}).interpret_default()
