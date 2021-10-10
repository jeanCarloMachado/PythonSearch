from typing import List

""" Centralize all execptions definitions to help in the data discovery """


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
    def key_does_not_exist(key: str, matches: List[str]):
        return RunException(
            f"Does pattern does not match 1 key ({key}) and ({matches})"
        )


class RegisterNewException(Exception):
    config = {
        "disable_tray_message": True,
        "enable_notification": True,
        "disable_sentry": True,
    }

    @staticmethod
    def empty_content():
        return RegisterNewException(f"Will not register as content looks too small")
