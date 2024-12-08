
from python_search.apps.theme.BaseTheme import BaseTheme

class NewLight(BaseTheme):
    def __init__(self):
        self.colors = {
            "backgroud": "#FFFFFF",
            "selected": "#E28A44",
            "query": "#EB727F",
            "query_enabled": "#d33682",
            "text": "#43444B",
            "partialmatch": "#AC8C4A",
            "entrycontentselected": "#83A96C",
            "entrycontentunselected": "#9FA0A7",
            "entrytype": "#9FA0A7",
            "cursor": "#A852B1",
            "green": "#97AE5E",
            "yellow": "#DB9D3E",
            "red": "#E56B55",
        }

        super().__init__()


class DesertTheme(BaseTheme):
    def __init__(self):
        self.colors = {
            "backgroud": "#303030",
            "selected": "#87D700",
            "query": "#87D700",
            "query_enabled": "#d33682",
            "partialmatch": "#D78701",
            "text": "#FFFFFF",
            "entrycontentselected": "#87D700",
            "entrycontentunselected": "#9FA0A7",
            "entrytype": "#9FA0A7",
            "cursor": "#AB5DAC",
            "green": "#97AE5E",
            "yellow": "#DB9D3E",
            "red": "#E56B55",
        }
        super().__init__()


class D2Theme(BaseTheme):
    def __init__(self):
        self.colors = {
            "backgroud": "#1C2918",
            "selected": "#5FDE33",
            "query": "#87D700",
            "query_enabled": "#d33682",
            "partialmatch": "#B3150C",
            "text": "#D7D2CA",
            "entrycontentselected": "#5FDE33",
            "entrycontentunselected": "#9FA0A7",
            "entrytype": "#B3150C",
            "cursor": "#CD0300",
            "green": "#65B0F4",
            "yellow": "#F5E359",
            "red": "#E90100",
        }
        super().__init__()


def get_current_theme() -> BaseTheme:
    from python_search.apps.theme.ThemeSelector import ThemeSelector
    return ThemeSelector().get_theme()
