import os

from search_run.logger import logger


def setup():
    """Enable data doc tracing
    Will only do something if th flag USE_DDTRACE is turned to ON
    """
    if os.getenv("USE_DDTRACE"):
        logger.info("Using ddtrace")

        from ddtrace import patch_all

        patch_all()
    else:
        logger.info("Not using ddtrace")
