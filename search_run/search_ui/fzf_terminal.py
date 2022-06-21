import datetime
import os

from search_run.config import PythonSearchConfiguration
from search_run.environment import is_mac
from search_run.observability.logger import logging


class FzfInTerminal:
    """
    Renders the search ui using fzf + termite terminal
    """

    FONT_SIZE = 15
    PREVIEW_PERCENTAGE_SIZE = 50
    HEIGHT = 270
    WIDTH = 1100

    configuration: PythonSearchConfiguration

    @staticmethod
    def build_search_ui(configuration) -> "FzfInTerminal":
        """Assembles what is specific for the search ui exclusively"""

        return FzfInTerminal(title=configuration.APPLICATION_TITLE)

    def __init__(self, *, title=""):
        self.height = FzfInTerminal.HEIGHT
        self.width = FzfInTerminal.WIDTH

        self.preview_cmd = f"search_run _utils preview_entry {{}} "
        self.executable = "search_run"
        self.title = title

    def run(self) -> None:
        self._launch_terminal(self.internal_cmd())

    def internal_cmd(self):
        return f"""bash -c '{self._get_rankging_generate_cmd()} | \
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
        --bind "enter:+reload:({self._get_rankging_generate_cmd()})" \
        --bind "enter:+clear-query" \
        --bind "esc:execute-silent:({self.executable} _utils hide_launcher)" \
        --bind "alt-enter:execute-silent:(nohup {self.executable} run_key {{}} --query_used {{q}} & disown)" \
        --bind "alt-m:execute-silent:(nohup {self.executable} edit_main {{}} & disown)" \
        --bind "alt-m:+execute-silent:({self.executable} _utils hide_launcher)" \
        --bind "ctrl-l:clear-query" \
        --bind "ctrl-l:+first" \
        --bind "ctrl-k:execute-silent:(nohup {self.executable} copy_key_only {{}} & disown)" \
        --bind "ctrl-c:execute-silent:(nohup {self.executable} copy_entry_content {{}} & disown)" \
        --bind "ctrl-c:+execute-silent:({self.executable} _utils hide_launcher)" \
        --bind "ctrl-e:execute-silent:(nohup {self.executable} edit_key {{}} & disown)" \
        --bind "ctrl-e:+execute-silent:({self.executable} _utils hide_launcher)" \
        --bind "ctrl-s:execute-silent:(nohup {self.executable} search_edit {{}} & disown)" \
        --bind "ctrl-s:+execute-silent:({self.executable} _utils hide_launcher)" \
        --bind "ctrl-r:reload:({self._get_rankging_generate_cmd(reload=True)})" \
        --bind "ctrl-t:execute-silent:(notify-send testjean)" \
        --bind "ctrl-g:execute-silent:( {self.executable} google_it {{q}} )" \
        --bind "ctrl-g:+execute-silent:({self.executable} _utils hide_launcher)" \
        --bind "ctrl-f:first" \
        --bind "shift-up:first" \
        --bind "ctrl-d:abort" '
        """


    def _get_rankging_generate_cmd(self, reload=False):
        # in mac we need tensorflow to be installed via conda
        if is_mac():
            if reload:
                return f'curl -s localhost:8000/ranking/reload_and_generate'

            return f'curl -s localhost:8000/ranking/generate'

        return f'{self.executable} ranking generate'

    def _launch_terminal(self, internal_cmd: str) -> None:

        font = "FontAwesome"
        if is_mac():
            font = "Monaco"

        launch_cmd = f"""nice -19 kitty \
        --title="{self.title} {datetime.datetime.now().isoformat()}"\
         -o remember_window_size=n \
        -o initial_window_width={self.width}  \
        -o initial_window_height={self.height} \
        -o font_family="{font}" \
        -o confirm_os_window_close=0 \
        -o font_size={FzfInTerminal.FONT_SIZE} \
         {internal_cmd}
        """
        logging.info(f"Command performed:\n {internal_cmd}")
        result = os.system(launch_cmd)
        if result != 0:
            raise Exception("Search run fzf projection failed")


if __name__ == "__main__":
    import fire

    fire.Fire()
