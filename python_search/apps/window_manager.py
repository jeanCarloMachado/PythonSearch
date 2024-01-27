import os


class WindowManager:
    """
    Abstract specific window manager calls and initiallization
    """

    @staticmethod
    def is_gnome():
        return 0 == os.system("wmctrl -m | grep -i gnome ")

    @staticmethod
    def is_xfce():
        return 0 == os.system("wmctrl -m | grep -i xfwm4")

    def hide_window(self, title):
        if self.is_gnome():
            return 0 == os.system(f"xdotool search --name '{title}' windowminimize")

        raise Exception("Window manager not supported")
