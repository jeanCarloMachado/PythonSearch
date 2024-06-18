import logging
import sys




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

    fh = logging.FileHandler("/tmp/debug_interpreter")
    fh.setLevel(logging.INFO)
    logger.addHandler(fh)

    return logger



def setup_data_writter_logger(event_name):
    logger = logging.getLogger(f"data-writer_{event_name}")

    fh = logging.FileHandler(f"/tmp/data-writer_event_{event_name}")
    fh.setLevel(logging.DEBUG)
    logger.addHandler(fh)

    logger.setLevel(logging.WARNING)

    return logger

