import logging
from subprocess import CalledProcessError
from typing import Optional

from grimoire.shell import shell as s
from grimoire.string import chomp, emptish
from search_run.exceptions import MenuException
from search_run.search_ui.interface import SearchInterface, SearchResult


class TermiteFzf(SearchInterface):
    """
    Renders the search ui using the termite terminal + fzf
    """
    def __init__(
            self, title="RunT: "
    ):
        self.title = title

    def run(
            self, cmd: str
    ) -> (str, str):


        # Tried things that did not work:
        termite_cmd = f"""termite --title=launcher -e "bash -c '{cmd} | fzf --print-query '"
        """

        try:
            result = s.check_output(termite_cmd)
        except CalledProcessError:
            return None

        logging.info(f"Rofi result: {result}")

        result = chomp(result)
        if emptish(result):
            raise MenuException.given_empty_value()

        return SearchResult(result)


