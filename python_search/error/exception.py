from functools import wraps
import os


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
                import sys, traceback

                send_notification(f"Exception {e}")
                os.system(f"echo '{traceback.format_exc()}' |  error_panel run")
                raise e
            return result

        return __

    return _
