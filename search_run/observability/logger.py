import logging
import sys


def configure_logger(name="default") -> logging.Logger:
    logger = logging.getLogger(name)
    logger.addHandler(logging.StreamHandler(sys.stdout))
    # use this for debug purposes
    # logger.setLevel(logging.DEBUG)
    logger.setLevel(logging.INFO)
    return logger


# this is the application default logger
logger = configure_logger()
