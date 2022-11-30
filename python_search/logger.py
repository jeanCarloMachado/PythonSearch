import logging


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
    logger.setLevel(logging.DEBUG)
    fh = logging.FileHandler("/tmp/run_key.txt")
    fh.setLevel(logging.DEBUG)
    ch = logging.StreamHandler()
    ch.setLevel(logging.INFO)
    logger.addHandler(fh)
    logger.addHandler(ch)

    return logger
