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
        termite_cmd = f"""termite --title=launcher -e "bash -c '{cmd} | \
        fzf --reverse --exact --no-sort --print-query  \
        > /tmp/termite_result'"
        """

        s.run(termite_cmd)
        result : str = s.check_output('cat /tmp/termite_result')

        logging.info(f"Rofi result: {result}")

        result = chomp(result)
        if emptish(result):
            raise MenuException.given_empty_value()

        result_lines = result.splitlines()
        return SearchResult(result=result_lines[1], query=result_lines[0])


