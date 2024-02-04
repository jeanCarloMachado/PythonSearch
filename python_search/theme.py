import datetime


class TimeBasedThemeSelector:
    def get_theme(self) -> str:
        """
        Returns the theme to use based on the current time
        """
        now = datetime.datetime.now()
        if now.hour > 18 or now.hour < 6:
            return "dracula"
        else:
            return "light"

class BaseTheme:
    colors = None


class LightTheme(BaseTheme):
    def __init__(self):
        self.colors = {
            'backgroud': "#FAFAFA",
            'selected': "#4F6CFF",
            'query': "#B98302",
            'entrycontentselected': "#0E87BE",
            'entrycontentunselected': "#9FA0A7",
            'partialmatch': "#E55C57",
            'text': "#43444B",
            'cursor': '#AD3DAB'
        }

        self.backgroud = self.colors['backgroud']
        self.text = self.colors['text']

        self.font_size = 16
        self.font = "Menlo"
    def get_colorful(self):
        import colorful as cf

        cf.update_palette(self.colors)
        return cf


class DesertTheme(BaseTheme):
    def __init__(self):
        self.colors = {
            'backgroud': "#303030",
            'selected': "#D78602",
            'partialmatch': "#608700",
            'text': "#FFFFFF",
            'query': "##608700",
        }

        self.backgroud = self.colors['backgroud']
        self.text = self.colors['text']

        self.font_size = 16
        self.font = "Menlo"
    def get_colorful(self):
        import colorful as cf

        cf.update_palette(self.colors)
        return cf