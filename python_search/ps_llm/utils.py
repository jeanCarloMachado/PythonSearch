def get_spark():
    from pyspark.sql.session import SparkSession

    return (
        SparkSession.builder.config("spark.executor.memory", "15g")
        .config("spark.driver.memory", "10g")
        .config("spark.memory.offHeap.enabled", True)
        .config("spark.memory.offHeap.size", "16g")
        .getOrCreate()
    )


import functools
import time


class Timer:
    """
    timer class
    """

    def __init__(self):
        """
        Starts the timer on a new instance
        """
        self.start_time = time.perf_counter()

    def report(self, identifier: str) -> None:
        end_time = time.perf_counter()
        run_time = end_time - self.start_time
        print(identifier + " took {} secs".format(round(run_time, 3)))


def timer(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.perf_counter()
        value = func(*args, **kwargs)
        end_time = time.perf_counter()
        run_time = end_time - start_time
        print("Finished {} in {} secs".format(repr(func.__name__), round(run_time, 3)))
        return value

    return wrapper
