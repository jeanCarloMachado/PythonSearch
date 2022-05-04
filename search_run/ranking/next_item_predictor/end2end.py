#!/usr/bin/env python
import logging
import sys

from search_run.observability.logger import initialize_logging

initialize_logging()


class EndToEnd:
    def run(self):
        logging.info("End to end ranking")
        pass


if __name__ == "__main__":
    import fire

    fire.Fire(EndToEnd)
