
import time
from functools import wraps
import os
from datetime import timedelta


def timeit(method):
    @wraps(method)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        result = method(*args, **kwargs)
        end_time = time.time()
        if os.getenv('ENABLE_TIME_IT'):
            print(f"{method.__name__} => {timedelta(milliseconds = ((end_time-start_time) * 1000))} s")

        return result

    return wrapper