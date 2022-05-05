import os
import sys

from search_run.base_configuration import PythonSearchConfiguration
from search_run.observability.logger import logging


class FzfInTerminal:
    """
    Renders the search ui using fzf + termite terminal
    """

    FONT_SIZE = 13
    PREVIEW_PERCENTAGE_SIZE = 50
    HEIGHT = 330

    configuration: PythonSearchConfiguration

    @staticmethod
    def build_search_ui(configuration) -> "FzfInTerminal":
        """Assembles what is specific for the search ui exclusively"""
        preview_cmd = "(echo '{}' | cut -d ':' -f1 --complement | jq . -C 2>/dev/null ) || echo {}"
        return FzfInTerminal(
            configuration=configuration,
            height=FzfInTerminal.HEIGHT,
            width=1100,
            preview_cmd=preview_cmd,
        )

    def __init__(self, *, configuration, height, width, preview_cmd):
        self.height = height
        self.width = width
        self.preview_cmd = preview_cmd
        self.executable = sys.argv[0]
        self.configuration = configuration

    def run(self) -> None:
        internal_cmd = f"""bash -c '{self.executable} ranking generate | \
        fzf \
        --tiebreak=length,begin,index \
        --cycle \
        --no-hscroll \
        --hscroll-off=0 \
        --preview "{self.preview_cmd}" \
        --preview-window=right,{FzfInTerminal.PREVIEW_PERCENTAGE_SIZE}%,wrap \
        --reverse -i --exact --no-sort \
        --border=none \
        --margin=0% \
        --padding=0% \
        --bind "enter:execute-silent:(nohup {self.executable} run_key {{}} --query_used {{q}} & disown)" \
        --bind "enter:+execute-silent:({self.executable} _utils hide_launcher)" \
        --bind "enter:+reload:({self.executable} ranking generate)" \
        --bind "enter:+clear-query" \
        --bind "alt-enter:execute-silent:(nohup {self.executable} run_key {{}} --query_used {{q}} & disown)" \
        --bind "ctrl-l:clear-query" \
        --bind "ctrl-l:+first" \
        --bind "ctrl-c:execute-silent:(nohup {self.executable} clipboard_key {{}} & disown)" \
        --bind "ctrl-c:+execute-silent:({self.executable} _utils hide_launcher)" \
        --bind "ctrl-e:execute-silent:(nohup {self.executable} edit_key {{}} & disown)" \
        --bind "ctrl-e:+execute-silent:({self.executable} _utils hide_launcher)" \
        --bind "ctrl-k:execute-silent:(nohup {self.executable} edit_key {{}} & disown)" \
        --bind "ctrl-k:+execute-silent:({self.executable} _utils hide_launcher)" \
        --bind "esc:execute-silent:({self.executable} _utils hide_launcher)" \
        --bind "ctrl-h:execute-silent:({self.executable} _utils hide_launcher)" \
        --bind "ctrl-r:reload:({self.executable} ranking generate)" \
        --bind "ctrl-n:reload:({self.executable} nlp get_read_projection_rank_for_query {{q}})" \
        --bind "ctrl-t:execute-silent:(notify-send test)" \
        --bind "ctrl-q:execute-silent:(notify-send {{q}})" \
        --bind "ctrl-f:first" \
        --bind "ctrl-d:abort" '
        """

        self._launch_terminal(internal_cmd)

    def _launch_terminal(self, internal_cmd: str):

        launch_cmd = f"""ionice -n 3 nice -19 kitty \
        --title={self.configuration.APPLICATION_TITLE} -o remember_window_size=n \
        -o initial_window_width={self.width}  \
        -o initial_window_height={self.height} \
        -o font_family="FontAwesome" \
        -o font_size={FzfInTerminal.FONT_SIZE} \
         {internal_cmd}
        """
        logging.info(f"Command performed:\n {internal_cmd}")
        result = os.system(launch_cmd)
        if result != 0:
            raise Exception("Search run fzf projection failed")
