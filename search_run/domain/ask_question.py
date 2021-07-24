from grimoire.desktop.dmenu import Dmenu
from grimoire.string import emptish


class AskQuestion:
    def ask(self, message: str) -> str:

        result = Dmenu(title=message).rofi()

        if emptish(result):
            raise AskQuestionException.empty_content()

        return result


class AskQuestionException(Exception):
    config = {
        "disable_tray_message": True,
        "enable_notification": True,
        "disable_sentry": True,
    }

    @staticmethod
    def empty_content():
        return AskQuestionException(
            f"The value you gave to dmenu looks empty. Will not proceed"
        )
