import datetime


class ThemeSelector:
    """
    A class that selects theme.
    If the user has a theme file in their home directory, it will use that theme.
    Otherwise, it will use the NewLight theme during the day and the Desert theme at night.

    Methods:
        get_theme(): Returns the theme to use based on the current time.
    """

    _HOUR_FROM = 8
    _HOUR_TO = 17

    def get_theme(self) -> str:
        """
        Returns the theme to use based on the current time.

        Returns:
            str: The selected theme.
        """
        import os

        home = os.environ["HOME"]
        if os.path.exists(home + "/.python_search/theme"):
            theme = open(home + "/.python_search/theme").read().strip()
            if theme == "Desert":
                return DesertTheme()
            elif theme == "D2":
                return D2Theme()

        now = datetime.datetime.now()
        if now.hour >= self._HOUR_FROM and now.hour <= self._HOUR_TO:
            return NewLight()
        else:
            return DesertTheme()


class BaseTheme:
    colors = None

    def get_colorful(self):
        import colorful as cf

        cf.update_palette(self.colors)
        return cf

    def __init__(self):
        self.backgroud = self.colors["backgroud"]
        self.text = self.colors["text"]

        self.font_size = 17
        self.font = "SF Pro"


class NewLight(BaseTheme):
    def __init__(self):
        self.colors = {
            "backgroud": "#FFFFFF",
            "selected": "#E28A44",
            "query": "#EB727F",
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
    return ThemeSelector().get_theme()
