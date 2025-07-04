import logging
import os
import sys


def setup_term_ui_logger():
    logger = logging.getLogger("term-ui")
    logger.setLevel(logging.INFO)

    ch = logging.StreamHandler()
    if os.environ.get("PS_DEBUG"):
        ch.setLevel(logging.INFO)
    else:
        ch.setLevel(logging.WARNING)
        
    logger.addHandler(ch)

    return logger

def setup_run_key_logger():
    """
    Code has to be fast
    """
    logger = logging.getLogger("run-key")

    ch = logging.StreamHandler()
    ch.setLevel(logging.WARNING)
    logger.addHandler(ch)

    logger.setLevel(logging.INFO)

    return logger


def interpreter_logger():
    logger = logging.getLogger("interpeter_logger")
    logger.setLevel(logging.INFO)

    ch = logging.StreamHandler(sys.stdout)
    ch.setLevel(logging.WARNING)
    logger.addHandler(ch)

    return logger


def setup_data_writter_logger(event_name):
    logger = logging.getLogger(f"data-writer_{event_name}")

    ch = logging.StreamHandler()
    if os.environ.get("PS_DEBUG"):
        ch.setLevel(logging.INFO)
    else:
        ch.setLevel(logging.WARNING)
    logger.addHandler(ch)
    logger.setLevel(logging.INFO)

    return logger
