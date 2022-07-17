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

    def generate(self):
        """
        Export a new configuration.

        You can customize the method of ranking.
        By default the ranking is just a projection of the data.
        But if you want to have better ranking you can pass "complete"
        the more expensive algorithm optimizing the ranking will be used.
        """
        if is_mac():
            Mac(self.configuration).generate()
            return

        if WindowManager.is_gnome():
            Gnome(self.configuration).generate()
            return

        if WindowManager.is_i3():
            I3(self.configuration).generate()
            return