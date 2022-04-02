import os

class I3:
    """
    Contain implementation of window manager necessary functions for i3
    The same interfaces could be implemented for other window managers
    """
    def focus_on_window_with_title(self, title) -> bool:
        """
        Try to focus on the window with the passed title, returns True if successful
        """
        cmd = f'wmctrl -a "{title}" '

        result = 0 == os.system(cmd)

        if result:
            self.show_window(title)

        return result

    def show_window(self, title) -> bool:
        return 0 == os.system(
            f"i3-msg '[title=\"{title}\"] scratchpad show'"
        )

    def hide_window(self, title) -> bool:
        return 0 == os.system(
            f'sleep 0.1; i3-msg "[title={title}] move scratchpad"'
        )

