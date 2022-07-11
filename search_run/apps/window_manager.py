import os


class WindowManager:
    """
    Abstract specific window manager calls and initiallization
    """

    @staticmethod
    def load_from_environment() -> "WindowManager":
        if WindowManager.is_i3():
            return I3()

        return Gnome()

    @staticmethod
    def is_i3():
        return not WindowManager.is_gnome()

    @staticmethod
    def is_gnome():
        return 0 == os.system("wmctrl -m | grep -i gnome ")

    def hide_window(self, title):
        raise Exception("Not implemented")


class I3(WindowManager):
    """
    Contains implementation of window manager necessary functions for i3
    The same interfaces could be implemented for other window managers
    """

    def focus_on_window_with_title(self, title) -> bool:
        """
        Try to focus on the window with the passed title, returns True if successful
        """
        cmd = f'wmctrl -a "{title}" '
        print("Focus on window with cmd:", cmd)

        result = 0 == os.system(cmd)

        if result:
            self.show_window(title)

        return result

    def show_window(self, title) -> bool:
        return 0 == os.system(
            f"unset I3SOCK ; i3-msg '[title=\"{title}\"] scratchpad show'"
        )

    def hide_window(self, title) -> bool:
        return 0 == os.system(
            f"sleep 0.1; i3-msg '[title=\"{title}\"]  move scratchpad'"
        )


class Gnome:
    """
    Contains implementation of window manager necessary functions for gnome
    The same interfaces could be implemented for other window managers
    """

    def hide_window(self, title) -> bool:
        return 0 == os.system(f"xdotool search --name '{title}' windowminimize")
