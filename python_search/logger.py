import logging


def setup_inference_logger():
    logger = logging.getLogger("inference")
    logger.setLevel(logging.DEBUG)
    fh = logging.FileHandler("/tmp/inference.txt")
    fh.setLevel(logging.DEBUG)
    ch = logging.StreamHandler()
    ch.setLevel(logging.INFO)
    logger.addHandler(fh)
    logger.addHandler(ch)

    return logger
