from search_run.search_ui.fzf_in_terminal import FzfInTerminal
from search_run.search_ui.interface import SearchInterface
from search_run.search_ui.rofi import Rofi


class UIFactory:
    @staticmethod
    def get_instance() -> SearchInterface:
        return UIFactory.get_fzf()

    @staticmethod
    def get_fzf():
        return FzfInTerminal()

    @staticmethod
    def get_rofi(self):
        return Rofi()
