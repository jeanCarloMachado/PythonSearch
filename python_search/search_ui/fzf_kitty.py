import os

from python_search.apps.terminal import Terminal
from python_search.configuration.configuration import PythonSearchConfiguration
from python_search.environment import is_mac


class FzfInKitty:
    """
    Renders the search ui using fzf + termite terminal
    """

    FONT_SIZE : int = 15
    _default_window_size = (800, 400)

    configuration: PythonSearchConfiguration

    def __init__(self, configuration: PythonSearchConfiguration):
        custom_window_size = configuration.get_window_size()
        self.width = custom_window_size[0] if custom_window_size else self._default_window_size[0]
        self.height = custom_window_size[1] if custom_window_size else self._default_window_size[1]

        self.title = configuration.APPLICATION_TITLE
        self.configuration = configuration

        import logging
        import sys

        logger = logging.getLogger(name="search_ui")
        logger.addHandler(logging.StreamHandler(sys.stdout))
        logger.setLevel(logging.DEBUG)

        self._logger = logger
        self._fzf = Fzf(configuration)

    def run(self) -> None:
        self._launch_terminal(self._fzf.get_cmd())

    def _get_background_color(self):
        if self.configuration.get_fzf_theme() == "light":
            return " -o background=#ffffff "

        if self.configuration.get_fzf_theme() == "dark":
            return " -o background=#000000 "

        return " "

    def _launch_terminal(self, internal_cmd: str) -> None:

        font = "FontAwesome"
        if is_mac():
            font = "Pragmata Pro"

        launch_cmd = f"""nice -19 kitty \
        --title {self.title} \
        -o draw_minimal_borders=no \
        -o window_padding_width=0  \
        -o placement_strategy=center \
        -o window_border_width=0 \
        -o window_padding_width=0 \
        -o hide_window_decorations=titlebar-only \
        -o background_opacity=1 \
        -o active_tab_title_template=none \
        -o initial_window_width={self.width}  \
        -o initial_window_height={self.height} \
        -o font_family="{font}" \
        {self._get_background_color()} \
        -o font_size={FzfInKitty.FONT_SIZE} \
        {Terminal.GLOBAL_TERMINAL_PARAMS} \
         {internal_cmd}
        """
        self._logger.info(f"Command performed:\n {internal_cmd}")
        result = os.system(launch_cmd)
        if result != 0:
            raise Exception("Search run fzf projection failed")

class Fzf:
    PREVIEW_PERCENTAGE_SIZE = 50
    RANK_TIE_BREAK: str = "begin,index"
    def __init__(self, configuration: PythonSearchConfiguration):
        self.configuration = configuration
        self.preview_cmd = f"python_search _preview_entry {{}} "

    def run(self):
        os.system(self.get_cmd())

    def get_cmd(self):
        cmd = f"""bash -c ' export SHELL=bash ; {self._get_rankging_generate_cmd()} | \
        fzf \
        --tiebreak={Fzf.RANK_TIE_BREAK} \
        --extended \
        --reverse \
        --no-separator \
        --info=inline \
        --cycle \
        --no-hscroll \
        --ellipsis='' \
        --hscroll-off=0 \
        --preview "{self.preview_cmd}" \
        --preview-window=right,{Fzf.PREVIEW_PERCENTAGE_SIZE}%,wrap,border-left \
        -i \
        --border=none \
        --margin=0% \
        --padding=0% \
        {self._run_key("enter")} \
        {self._run_key("double-click")} \
        {self._edit_key('ctrl-e')} \
        {self._edit_key('right-click')} \
        --bind "alt-enter:execute-silent:(nohup python_search run_key {{}} --query_used {{q}} & disown)" \
        --bind "alt-m:execute-silent:(nohup python_search edit_main {{}} & disown)" \
        --bind "ctrl-l:clear-query" \
        --bind "ctrl-l:+first" \
        --bind "ctrl-k:execute-silent:(python_search _copy_key_only {{}} && kill -9 $PPID)" \
        --bind "ctrl-c:execute-silent:(nohup python_search _copy_entry_content {{}} && kill -9 $PPID)" \
        --bind "ctrl-s:execute-silent:(nohup python_search search_edit {{}} && kill -9 $PPID)" \
        --bind "ctrl-r:reload:({self._get_rankging_generate_cmd(reload=True)})" \
        --bind "ctrl-f:first" \
        --bind "shift-up:first" \
        --bind "esc:abort" \
        --bind "ctrl-d:abort"  \
        {self._get_fzf_theme()} ; exit 0
        '
        """

        return cmd

    def _get_fzf_theme(self):
        if self.configuration.get_fzf_theme() == "light":
            return ' --color="fg:#4d4d4c,bg:#ffffff,hl:#d7005f,info:#4271ae,prompt:#8959a8,pointer:#d7005f,marker:#4271ae,spinner:#4271ae,header:#4271ae,fg+:#4d4d4c,bg+:#ffffff,hl+:#d7005f" '

        if self.configuration.get_fzf_theme() == "dark":
            return ' --color="fg:#f8f8f2,bg:#282a36,hl:#bd93f9,fg+:#f8f8f2,bg+:#44475a,hl+:#bd93f9,info:#ffb86c,prompt:#50fa7b,pointer:#ff79c6,marker:#ff79c6,spinner:#ffb86c,header:#6272a4" '

        return " "

    def _run_key(self, shortcut) -> str:
        return f"""--bind "{shortcut}:execute-silent:(run_key {{}} --query_used {{q}} --fzf_pid_to_kill $PPID {{}} &)"  """

    def _edit_key(self, shortcut) -> str:
        return f"""--bind "{shortcut}:execute-silent:(nohup python_search edit_key --fzf_pid_to_kill $PPID {{}}  & disown)" """

    def _get_rankging_generate_cmd(self, reload=False):
        # in mac we need tensorflow to be installed via conda
        if self.configuration.use_webservice:

            if reload:
                return f"curl -s localhost:8000/ranking/reload_and_generate"

            return f"curl -s localhost:8000/ranking/generate"
        else:
            return f"python_search _ranking search"


if __name__ == "__main__":
    import fire

    fire.Fire()
