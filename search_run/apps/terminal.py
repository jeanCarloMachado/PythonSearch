
class Terminal:
    """
    Terminal abstraction for search run
    """

    def wrap_cmd_into_terminal(
        self, cmd, title=None, hold_terminal_open_on_end=True
    ) -> str:
        """
        wraps the command in a terminal but does not execute it
        """
        cmd = f'bash -c "{cmd}"'

        hold = ''
        if hold_terminal_open_on_end:
            hold = ' --hold '

        final_cmd = f'kitty {hold} -T "{title}" {cmd} '

        return final_cmd
