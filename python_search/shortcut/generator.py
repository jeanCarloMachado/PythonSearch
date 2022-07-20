from python_search.apps.window_manager import WindowManager
from python_search.entries_group import EntriesGroup
from python_search.environment import is_mac
from python_search.shortcut.gnome import Gnome
from python_search.shortcut.i3 import I3
from python_search.shortcut.mac import Mac


class ShortcutGenerator:
    """
    Generate shortcuts for python search
    """

    def __init__(self, configuration: EntriesGroup):
        self.configuration = configuration
        self.mac = Mac(self.configuration)
        self.gnome = Gnome(self.configuration)
        self.i3 = I3(self.configuration)

    def generate(self):
        if is_mac():
            self.mac.generate()
            return

        if WindowManager.is_gnome():
            self.gnome.generate()
            return

        if WindowManager.is_i3():
            self.i3.generate()
            return
