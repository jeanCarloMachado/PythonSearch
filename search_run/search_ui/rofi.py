import logging
from subprocess import CalledProcessError
from typing import Optional

from grimoire.shell import shell as s
from grimoire.string import chomp, emptish

from search_run.entities import SearchResult
from search_run.exceptions import MenuException
from search_run.search_ui.interface import SearchInterface


class Rofi(SearchInterface):
    def __init__(self, title="Run: "):
        self.title = title

    def run(self, cmd: Optional[str] = None) -> str:

        entries_cmd = ""

        # Tried things that did not work:
        rofi_cmd = f"""{entries_cmd} nice -19 rofi\
          -width 1000\
          -no-filter\
          -no-lazy-grab -i\
          -show-match\
          -no-sort\
          -dpi 120\
          -no-levenshtein-sort\
          -sorting-method fzf\
          -dmenu\
          -p '{self.title}'"""

        rofi_cmd = f"{cmd} | {rofi_cmd}"

        try:
            result = s.check_output(rofi_cmd)
        except CalledProcessError:
            return None

        logging.info(f"Rofi result: {result}")

        result = chomp(result)
        if emptish(result):
            raise MenuException.given_empty_value()

        return SearchResult(result=result, query="")
