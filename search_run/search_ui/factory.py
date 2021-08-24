
from  search_run.search_ui.interface import SearchInterface
from  search_run.search_ui.termite_fzf import TermiteFzf
from  search_run.search_ui.rofi import Rofi

class UIFactory:
    @staticmethod
    def get_instance() -> SearchInterface:
        return Rofi()
        #return TermiteFzf()