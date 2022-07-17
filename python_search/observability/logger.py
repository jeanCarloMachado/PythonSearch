import logging
import sys

from python_search.environment import is_mac

SYSLOG_IDENTIFIER = "python-search"


def setup_systemd_handler():
    if is_mac():
        return

    # systemd only works for linux
    from systemd.journal import JournalHandler

    return JournalHandler(SYSLOG_IDENTIFIER=SYSLOG_IDENTIFIER)


def initialize_logging():

    """Updates the global logging module"""
    handlers = [
        logging.StreamHandler(sys.stdout),
    ]
    if not is_mac():
        handlers.append(setup_systemd_handler())

    logging.basicConfig(level=logging.INFO, handlers=handlers)

    return logging


def initialize_systemd_logging():
    return initialize_logging()
