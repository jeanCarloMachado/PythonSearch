import os

from grimoire.shell import shell as s
from grimoire.string import chomp, emptish

from search_run.entities import SearchResult
from search_run.exceptions import MenuException
from search_run.logger import logger
from search_run.search_ui.interface import SearchInterface


class FzfInTerminal(SearchInterface):
    """
    Renders the search ui using fzf + termite terminal
    """

    HEIGHT = 500
    WIDTH = 1100

    def __init__(self, title="RunT: "):
        self.title = title

    def run(self, cmd: str) -> (str, str):

        launch_cmd = f"""
        ionice -n 3 nice -19 kitty --title=launcher -o remember_window_size=n \
        -o initial_window_width={FzfInTerminal.WIDTH}  \
        -o  initial_window_height={FzfInTerminal.HEIGHT} \
        bash -c '{cmd} | \
        fzf \
            --bind "enter:execute-silent:(nohup search_run run_key {{}} & disown)" \
            --preview "echo {{}} | cut -d \':\' -f1 --complement | jq . " \
            --preview-window=right,40% \
            --reverse -i --exact --no-sort'
            """
        logger.info(f"{launch_cmd}")
        os.system(launch_cmd)

        return
        with open("/tmp/search_run_result") as file:
            result = file.read()
            logger.info(f"Result: {result}")

        result = chomp(result)
        # the terminal result from fzf is the first line having the query and the second the matched result
        result_lines = result.splitlines()

        if emptish(result):
            raise MenuException.given_empty_value()
        return SearchResult(result=result_lines[1], query=result_lines[0])
