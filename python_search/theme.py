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
