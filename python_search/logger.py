import logging
import sys


def setup_inference_logger():
    logger = logging.getLogger("inference")
    logger.setLevel(logging.DEBUG)

    # fh = logging.FileHandler("/tmp/inference.txt")
    # fh.setLevel(logging.DEBUG)
    # logger.addHandler(fh)

    ch = logging.StreamHandler()
    ch.setLevel(logging.INFO)
    logger.addHandler(ch)

    return logger


def setup_preview_logger():
    """
    Only writes to file
    """
    logger = logging.getLogger("preview")
    fh = logging.FileHandler("/tmp/preview.txt")
    fh.setLevel(logging.INFO)
    logger.addHandler(fh)

    return logger


def setup_run_key_logger():
    logger = logging.getLogger("run-key")
    fh = logging.FileHandler("/tmp/run_key.txt")
    fh.setLevel(logging.DEBUG)
    logger.addHandler(fh)

    return logger


def setup_data_writter_logger(event_name):
    logger = logging.getLogger(f"data-writer_{event_name}")
    logger.setLevel(logging.DEBUG)
    fh = logging.FileHandler(f"/tmp/data-writer_event_{event_name}")
    fh.setLevel(logging.DEBUG)
    ch = logging.StreamHandler()
    ch.setLevel(logging.INFO)
    logger.addHandler(fh)
    logger.addHandler(ch)

    return logger


class StreamToLogger(object):
    """
    Fake file-like stream object that redirects writes to a logger instance.
    """

    def __init__(self, logger, level):
        self.logger = logger
        self.level = level
        self.linebuf = ""

    def write(self, buf):
        for line in buf.rstrip().splitlines():
            self.logger.log(self.level, line.rstrip())

    def flush(self):
        pass
