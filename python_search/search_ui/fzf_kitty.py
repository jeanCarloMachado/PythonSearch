import os

from python_search.apps.terminal import Terminal
from python_search.config import PythonSearchConfiguration
from python_search.environment import is_mac


class FzfInKitty:
    """
    Renders the search ui using fzf + termite terminal
    """

    FONT_SIZE = 15
    PREVIEW_PERCENTAGE_SIZE = 50
    HEIGHT = 127
    WIDTH = 950

    configuration: PythonSearchConfiguration

    @staticmethod
    def build_search_ui(configuration) -> "FzfInKitty":
        """Assembles what is specific for the search ui exclusively"""

        return FzfInKitty(configuration=configuration)

    def __init__(self, *, configuration: PythonSearchConfiguration):
        self.height = FzfInKitty.HEIGHT
        self.width = FzfInKitty.WIDTH

        self.preview_cmd = f"python_search _preview_entry {{}} "
        self.executable = "python_search"
        self.title = configuration.APPLICATION_TITLE
        self.configuration = configuration

        import logging
        import sys

        logger = logging.getLogger(name="search_ui")
        logger.addHandler(logging.StreamHandler(sys.stdout))
        logger.setLevel(logging.DEBUG)

        self._logger = logger

    def run(self) -> None:
        self._launch_terminal(self._fzf_cmd())

    def _fzf_cmd(self):
        FZF_LIGHT_THEME = "fg:#4d4d4c,bg:#ffffff,hl:#d7005f,info:#4271ae,prompt:#8959a8,pointer:#d7005f,marker:#4271ae,spinner:#4271ae,header:#4271ae,fg+:#4d4d4c,bg+:#ffffff,hl+:#d7005f"
        THEME = f"--color={FZF_LIGHT_THEME}"  # for more fzf options see: https://www.mankier.com/1/fzf#
        cmd = f"""bash -c 'pkill fzf ; export SHELL=bash ; {self._get_rankging_generate_cmd()} | \
        fzf \
        --tiebreak=length,begin,index \
        --cycle \
        --no-hscroll \
        --hscroll-off=0 \
        --preview "{self.preview_cmd}" \
        --preview-window=right,{FzfInKitty.PREVIEW_PERCENTAGE_SIZE}%,wrap,border-left \
        --reverse -i --exact --no-sort \
        --border=none \
        --margin=0% \
        --padding=0% \
        {self._run_key("enter")} \
        {self._run_key("double-click")} \
        {self._edit_key('ctrl-e')} \
        {self._edit_key('right-click')} \
        --bind "alt-enter:execute-silent:(nohup {self.executable} run_key {{}} --query_used {{q}} & disown)" \
        --bind "alt-m:execute-silent:(nohup {self.executable} edit_main {{}} & disown)" \
        --bind "alt-m:+execute-silent:({self.executable} _utils hide_launcher)" \
        --bind "ctrl-l:clear-query" \
        --bind "ctrl-l:+first" \
        --bind "ctrl-k:execute-silent:(nohup {self.executable} _copy_key_only {{}} & disown)" \
        --bind "ctrl-k:+clear-query" \
        --bind "ctrl-c:execute-silent:(nohup {self.executable} _copy_entry_content {{}} & disown)" \
        --bind "ctrl-c:+clear-query" \
        --bind "ctrl-s:execute-silent:(nohup {self.executable} search_edit {{}} & disown)" \
        --bind "ctrl-s:+execute-silent:({self.executable} _utils hide_launcher)" \
        --bind "ctrl-r:reload:({self._get_rankging_generate_cmd(reload=True)})" \
        --bind "ctrl-t:execute-silent:(notify-send testjean)" \
        --bind "ctrl-f:first" \
        --bind "shift-up:first" \
        --bind "esc:abort" \
        --bind "ctrl-d:abort"  \
        {THEME}  ; exit 0
        '
        """

        self._logger.info("Cmd: ", cmd)
        return cmd

    def _run_key(self, shortcut) -> str:
        return f"""--bind "{shortcut}:execute-silent:(LOG_FILE=/tmp/log_run_key_fzf nohup {self.executable} run_key {{}} --query_used {{q}} & disown)" \
        --bind "{shortcut}:+execute-silent:({self.executable} _utils hide_launcher)" \
        --bind "{shortcut}:+reload:({self._get_rankging_generate_cmd()})" \
        --bind "{shortcut}:+clear-query" \
        --bind "{shortcut}:+abort"   """

    def _edit_key(self, shortcut) -> str:
        return f"""--bind "{shortcut}:execute-silent:(nohup {self.executable} edit_key {{}} & disown)" \
        --bind "{shortcut}:+execute-silent:({self.executable} _utils hide_launcher)"  """

    def _get_rankging_generate_cmd(self, reload=False):
        # in mac we need tensorflow to be installed via conda
        if self.configuration.supported_features.is_dynamic_ranking_supported():
            if reload:
                return f"curl -s localhost:8000/ranking/reload_and_generate"

            return f"curl -s localhost:8000/ranking/generate"

        return f"{self.executable} ranking generate"

    def _launch_terminal(self, internal_cmd: str) -> None:

        font = "FontAwesome"
        if is_mac():
            font = "Pragmata Pro"

        launch_cmd = f"""nice -19 kitty \
        --title="{self.title}"\
        -o draw_minimal_borders=yes \
        -o placement_strategy=top-left \
        -o window_border_width=0 \
        -o window_padding_width=0 \
        -o hide_window_decorations=titlebar-only \
        -o background_opacity=1 \
        -o tab_bar_style=hidden  \
        -o initial_window_width={self.width}  \
        -o initial_window_height={self.height} \
        -o font_family="{font}" \
        -o font_size={FzfInKitty.FONT_SIZE} \
        {Terminal.GLOBAL_TERMINAL_PARAMS} \
         {internal_cmd}
        """
        self._logger.info(f"Command performed:\n {internal_cmd}")
        result = os.system(launch_cmd)
        if result != 0:
            raise Exception("Search run fzf projection failed")


if __name__ == "__main__":
    import fire

    fire.Fire()