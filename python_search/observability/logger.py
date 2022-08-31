import logging
import sys

from python_search.environment import is_mac

SYSLOG_IDENTIFIER = "python-search"


def initialize_logging():

    """Updates the global logging module"""
    handlers = [
        logging.StreamHandler(sys.stdout),
    ]
    logging.basicConfig(level=logging.INFO, handlers=handlers)

    return logging


def initialize_systemd_logging():
    return initialize_logging()
