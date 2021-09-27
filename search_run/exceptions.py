from typing import List


class MenuException(Exception):
    config = {
        "disable_tray_message": True,
        "enable_notification": True,
        "disable_sentry": True,
    }

    @staticmethod
    def given_empty_value():
        return MenuException("No option selected in search ui!")


class CommandDoNotMatchException(Exception):
    pass


class RunException(Exception):
    @staticmethod
    def key_does_not_match(key: str, matches: List[str]):
        return RunException(
            f"Does pattern does not match 1 key ({key}) and ({matches})"
        )