class Terminal:
    """ Terminal abstraction for search run. """

    DEFAULT_TITLE = "SearchRunTerminal"

    def wrap_cmd_into_terminal(
        self, cmd, title=None, hold_terminal_open_on_end=True, return_command=False
    ) -> str:
        """
        if return_command = True does not execute the command rather just return it.
        """
        if hold_terminal_open_on_end:
            cmd = f" {cmd}"

        final_cmd = f'kitty -T "{title}" bash -c "{cmd}" '

        return final_cmd
