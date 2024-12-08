from python_search.apps.theme.theme import D2Theme, DesertTheme, NewLight


import datetime
import os


class ThemeSelector:
    """
    A class that selects theme.
    If the user has a theme file in their home directory, it will use that theme.
    Otherwise, it will use the NewLight theme during the day and the Desert theme at night.

    Methods:
        get_theme(): Returns the theme to use based on the current time.
    """

    _HOUR_FROM = 8
    _HOUR_TO = 15

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