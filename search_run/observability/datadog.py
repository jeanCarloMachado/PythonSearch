import os

from search_run.observability.logger import logger


def setup():
    """Enable data doc tracing
    Will only do something if th flag USE_DDTRACE is turned to ON
    """
    if os.getenv("USE_DDTRACE"):
        logger.debug("Using ddtrace")

        from ddtrace import patch_all

        patch_all()
    else:
        logger.debug("Not using ddtrace")
