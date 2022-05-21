import logging
import sys

from systemd.journal import JournalHandler

SYSLOG_IDENTIFIER = "python-search"


def initialize_logging():
    """Updates the global logging module"""
    logging.basicConfig(
        level=logging.INFO,
        handlers=[
            logging.StreamHandler(sys.stdout),
            JournalHandler(SYSLOG_IDENTIFIER=SYSLOG_IDENTIFIER),
        ],
    )

    return logging


def initialize_systemd_logging():
    log = logging.getLogger("systemd")
    log.addHandler(JournalHandler(SYSLOG_IDENTIFIER=SYSLOG_IDENTIFIER))
    log.setLevel(logging.INFO)
    return log
