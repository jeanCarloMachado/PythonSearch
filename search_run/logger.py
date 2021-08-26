import logging
import sys


def configure_logger() -> logging.Logger:
    logger = logging.getLogger("ranking")
    logger.addHandler(logging.StreamHandler(sys.stdout))
    # use this for debug purposes
    # logger.setLevel(logging.DEBUG)
    logger.setLevel(logging.INFO)
    return logger
