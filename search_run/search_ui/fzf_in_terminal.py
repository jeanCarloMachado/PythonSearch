import logging

from grimoire.shell import shell as s
from grimoire.string import chomp, emptish
from search_run.exceptions import MenuException
from search_run.search_ui.interface import SearchInterface
from search_run.entities import SearchResult


class FzfInTerminal(SearchInterface):
    """
    Renders the search ui using fzf + termite terminal
    """
    def __init__(
            self, title="RunT: "
    ):
        self.title = title

    def run(
            self, cmd: str
    ) -> (str, str):


        termite_cmd = f"""kitty --title=launcher -o remember_window_size=n \
        -o initial_window_width=1300 -o transparency=yes -o  initial_window_height=500 \
        bash -c '{cmd} | \
        fzf --reverse --exact --no-sort --print-query \
        > /tmp/termite_result'
        """

        s.run(termite_cmd)
        result : str = s.check_output('cat /tmp/termite_result')
        logging.info(f"Result: {result}")
        result = chomp(result)

        # the terminal result from fzf is the first line having the query and the second the matched result
        result_lines = result.splitlines()

        if emptish(result):
            raise MenuException.given_empty_value()
        return SearchResult(result=result_lines[1], query=result_lines[0])


