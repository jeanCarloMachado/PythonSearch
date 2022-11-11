""" Centralize all exceptions definitions to help in the _entries discovery """


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


class MissingConfigException:
    @staticmethod
    def configuration_not_set():
        raise MissingConfigException(
            "The python search configuration was not found. Run python_search setup to initialize a new config"
        )


from functools import wraps


def notify_exception():
    """
    Will let you know when a function is called or returned error as a desktop notification
    """

    def _(func):
        @wraps(func)
        def __(*args, **kwargs):
            try:
                result = func(*args, **kwargs)
            except Exception as e:
                from python_search.apps.notification_ui import send_notification

                send_notification(f"Exception: {str(e)}")
                raise e
            return result

        return __

    return _
