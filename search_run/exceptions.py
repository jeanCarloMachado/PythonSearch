""" Centralize all exceptions definitions to help in the data discovery """


class MenuException(Exception):
    @staticmethod
    def given_empty_value():
        return MenuException("No option selected in search ui!")


class CommandDoNotMatchException(Exception):
    @staticmethod
    def not_valid_command(entity, cmd):
        return CommandDoNotMatchException(
            f"Not Valid {entity.__class__.__name__} command {cmd}"
        )


class RunException(Exception):
    @staticmethod
    def key_does_not_exist(key: str):
        return RunException(f"Key does not exist: {key}")


class RegisterNewException(Exception):
    @staticmethod
    def empty_content():
        return RegisterNewException(f"Will not register as content looks too small")
