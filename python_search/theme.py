import datetime

class TimeBasedThemeSelector:
    HOUR_FROM = 8
    HOUR_TO = 17
    def get_theme(self) -> str:
        """
        Returns the theme to use based on the current time
        """
        now = datetime.datetime.now()
        if now.hour >= self.HOUR_FROM and now.hour <= self.HOUR_TO:
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

        self.font_size = 16
        self.font = "Menlo"


class OneLight(BaseTheme):
    def __init__(self):
        self.colors = {
            "backgroud": "#FAFAFA",
            "selected": "#4F6CFF",
            "query": "#B98302",
            "text": "#43444B",
            "partialmatch": "#E55C57",
            "entrycontentselected": "#0E87BE",
            "entrycontentunselected": "#9FA0A7",
            "entrytype": "#9FA0A7",
            "cursor": "#AD3DAB",
        }

        super().__init__()


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
        }
        super().__init__()


def get_current_theme():
    return TimeBasedThemeSelector().get_theme()
