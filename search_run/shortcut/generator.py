from search_run.apps.window_manager import WindowManager
from search_run.entries_group import EntriesGroup
from search_run.environment import is_mac
from search_run.shortcut.gnome import Gnome
from search_run.shortcut.i3 import I3
from search_run.shortcut.mac import Mac


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
