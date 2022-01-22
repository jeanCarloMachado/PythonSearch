from grimoire.shell import shell


class Browser:
    def open(self, url, app_mode=False, get_command_only=False):
        """
        if get_command_only is true returns the command to execute rather than executing it

        """
        cmd = self.open_get_command(url, app_mode, get_command_only)

        return shell.run(cmd)

    def open_get_command(self, url, app_mode=False, get_command_only=False):
        """
        if get_command_only is true returns the command to execute rather than executing it

        """
        program_to_open_with = "browser"
        if app_mode:
            program_to_open_with = "chromeAppMode"

        return f'runFunction {program_to_open_with} "{url}"'
