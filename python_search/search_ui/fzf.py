import os

from python_search.configuration.configuration import PythonSearchConfiguration
from python_search.environment import is_mac


class Fzf:
    PREVIEW_PERCENTAGE_SIZE = 50
    RANK_TIE_BREAK: str = "begin,index"

    def __init__(self, configuration: PythonSearchConfiguration):
        self.configuration = configuration
        self.preview_cmd = f"python_search _preview_entry {{}} "

    def run(self):
        os.system(self.get_cmd())

    def get_cmd(self):
        cmd = f"""bash -c 'export SHELL=bash ; {self._get_rankging_generate_cmd()} | \
        {self.get_fzf_cmd()} \
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
        {self._run_key("enter", kill_window=False)} \
        {self._run_key("double-click")} \
        {self._edit_key('ctrl-e')} \
        {self._edit_key('right-click')} \
        --bind "ctrl-l:clear-query" \
        --bind "ctrl-l:+first" \
        --bind "ctrl-j:down" \
        --bind "ctrl-k:up" \
        --bind "ctrl-c:execute-silent:(nohup python_search _copy_entry_content {{}} && kill -9 $PPID)" \
        --bind "ctrl-y:execute-silent:(python_search _copy_key_only {{}} && kill -9 $PPID)" \
        --bind "ctrl-r:reload-sync:({self._get_rankging_generate_cmd(reload=True)})" \
        --bind "ctrl-f:first" \
        --bind "shift-up:first" \
        --bind "esc:abort" \
        --bind "ctrl-d:abort"  \
        {self._get_fzf_theme()} ; rm -rf /tmp/mykitty ; exit 0
        '
        """

        return cmd

    def get_fzf_cmd(self):
        if is_mac():
            return "/opt/homebrew/bin/fzf"

        return "fzf"

    def _run_key(self, shortcut: str, kill_window=False) -> str:

        kill_expr = ""
        if kill_window:
            kill_expr = " --fzf_pid_to_kill $PPID "

        return f"""--bind "{shortcut}:execute-silent:(run_key {{}} --query_used {{q}} {kill_expr} {{}} &)" \
        --bind "{shortcut}:+reload-sync:(sleep 3 && {self._get_rankging_generate_cmd(reload=True)})" \
        --bind "{shortcut}:+first" \
        --bind "{shortcut}:+clear-screen" """

    def _edit_key(self, shortcut) -> str:
        return f' --bind "{shortcut}:execute-silent:(nohup entries_editor edit_key {{}} & disown )" '

    def _get_fzf_theme(self):
        if self.configuration.get_fzf_theme() == "light":
            return ' --color="fg:#4d4d4c,bg:#ffffff,hl:#d7005f,info:#4271ae,prompt:#8959a8,pointer:#d7005f,marker:#4271ae,spinner:#4271ae,header:#4271ae,fg+:#4d4d4c,bg+:#ffffff,hl+:#d7005f" '

        if self.configuration.get_fzf_theme() == "dracula":
            return ' --color="fg:#f8f8f2,bg:#282a36,hl:#bd93f9,fg+:#f8f8f2,bg+:#44475a,hl+:#bd93f9,info:#ffb86c,prompt:#50fa7b,pointer:#ff79c6,marker:#ff79c6,spinner:#ffb86c,header:#6272a4" '

        return " "

    def _get_rankging_generate_cmd(self, reload=False):
        # in mac we need tensorflow to be installed via conda
        if self.configuration.use_webservice:

            if reload:
                return "curl -s localhost:8000/ranking/reload_and_generate || python_search _ranking search"

            return "(curl -s localhost:8000/ranking/generate || python_search _ranking search)"


        else:
            return f"python_search _ranking search"
