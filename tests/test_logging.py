
def test_logging():
    from search_run.observability.logger import logging
    logging.info("Test logging ")

if __name__ == "__main__":
    import fire

    fire.Fire()
