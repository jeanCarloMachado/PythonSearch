import os
import sys

from python_search.configuration.configuration import PythonSearchConfiguration
from python_search.environment import is_mac


class Fzf:
    PREVIEW_PERCENTAGE_SIZE = 45
    RANK_TIE_BREAK: str = "index"

    def __init__(self, configuration: PythonSearchConfiguration):
        self.configuration = configuration
        self.preview_cmd = f"python_search _preview_entry {{}} "

    def run(self):
        cmd = self.get_cmd()

        os.system(cmd)

    def get_cmd(self):
        on_change = " "
        if self.configuration.is_on_change_rank_enabled():
            on_change = '  --bind "change:reload-sync:(entry_generator generate_for_fzf {{q}}  & ps_search )" '

        cmd = f"""bash -c 'export SHELL=bash ; ps_search --fast_mode=True  | \
        {self.get_fzf_cmd()} \
        --scheme=default \
        --tiebreak={Fzf.RANK_TIE_BREAK} \
        --extended \
        --layout=reverse \
        --info=inline \
        --cycle \
        --no-hscroll \
        --preview "{self.preview_cmd}" \
        --preview-window=right,{Fzf.PREVIEW_PERCENTAGE_SIZE}%,wrap,border-left \
        --ellipsis='' \
        --hscroll-off=0 \
        -i \
        --border=none \
        --margin=0% \
        --padding=0% \
        {self._run_key("enter")} \
        {self._run_key("double-click")} \
        {self._edit_key('ctrl-e')} \
        {self._edit_key('right-click')} \
        --bind "ctrl-l:clear-query" \
        --bind "ctrl-l:+clear-screen" \
        --bind "ctrl-l:+first" \
        --bind "ctrl-f:first" \
        --bind "ctrl-j:down" \
        --bind "ctrl-k:up" \
        --bind "ctrl-c:execute-silent:(nohup python_search _copy_entry_content {{}})" \
        --bind "ctrl-n:execute-silent:(nohup register_new launch_from_fzf {{}} & )" \
        --bind "ctrl-g:execute-silent:(google_it search {{q}})" \
        --bind "ctrl-d:execute-silent:(monorepo_cli  register_german {{q}} &)" \
        --bind "ctrl-y:execute-silent:(python_search _copy_key_only {{}})" \
        --bind "ctrl-r:reload-sync:(ps_search --reload_enabled=True)" \
        --bind "ctrl-n:reload-sync:(ps_search)" \
        --bind "ctrl-s:execute-silent:(nohup share_entry share_key {{}})" \
        {on_change} \
        --bind "shift-up:first" \
        --bind "esc:execute-silent:(ps_fzf hide_current_focused_window)" \
        --bind "esc:+clear-query" \
        --bind "ctrl-k:abort" \
        {self._get_fzf_theme()} ; exit 0
        '
        """
        if "ONLY_PRINT" in os.environ:
            print(cmd)
            sys.exit(0)

        return cmd

    def get_fzf_cmd(self):
        if is_mac():
            HOME = os.environ["HOME"]
            return f"{HOME}/.fzf/bin/fzf"

        return "fzf"

    def _run_key(self, shortcut: str, wrap_in_terminal=False) -> str:
        wrap_in_terminal_expr = ""
        if wrap_in_terminal:
            wrap_in_terminal_expr = " --wrap_in_terminal=True "

        return f"""--bind "{shortcut}:execute-silent:(nohup run_key {{}}  --query_used {{q}} {wrap_in_terminal_expr} {{}} &)" \
        --bind "{shortcut}:+reload-sync:(sleep 3 && ps_search)" \
        --bind "{shortcut}:+first" """

    def _edit_key(self, shortcut) -> str:
        return f''' --bind "{shortcut}:execute-silent:(entries_editor edit_key {{}} & disown )" \
                    --bind "{shortcut}:+reload-sync:(sleep 7 && ps_search --fast_mode=True)" '''
    def _get_fzf_theme(self):
        if self.configuration.get_fzf_theme() == "light":
            return "--color=bg+:#ffffff,bg:#ffffff,hl:#719872,fg:#616161,header:#719872,info:#727100,pointer:#E12672,marker:#E17899,fg+:#616161,preview-bg:#ffffff,prompt:#0099BD,hl+:#719899"


        if self.configuration.get_fzf_theme() in ["solarized"]:
            theme = Theme().solarized()
            return f' --color="fg:{theme.fg},bg:{theme.bg},hl:{theme.hl},fg+:{theme.fg_plus},bg+:{theme.bg_plus},hl+:{theme.hl_plus},info:{theme.info},prompt:{theme.prompt_arrows},pointer:{theme.pointer_current_line},marker:{theme.marker},spinner:{theme.spinner},header:{theme.header},query:{theme.query},label:{theme.label},border:{theme.border}" '

        if self.configuration.get_fzf_theme() in ["dark", "dracula"]:
            return ' --color="fg:#f8f8f2,bg:#282a36,hl:#bd93f9,fg+:#f8f8f2,bg+:#44475a,hl+:#bd93f9,info:#ffb86c,prompt:#50fa7b,pointer:#ff79c6,marker:#ff79c6,spinner:#ffb86c,header:#586e75" '

        return " "


class Theme:
    """
       fg                  Text
         preview-fg        Preview window text
       bg                  Background
         preview-bg        Preview window background
       hl                  Highlighted substrings
       fg+                 Text (current line)
       bg+                 Background (current line)
         gutter            Gutter on the left
       hl+                 Highlighted substrings (current line)
       query               Query string
         disabled          Query string when search is disabled (--disabled)
       info                Info line (match counters)
       border              Border around the window (--border and --preview)
         scrollbar         Scrollbar
         preview-border    Border around the preview window (--preview)
         preview-scrollbar Scrollbar
         separator         Horizontal separator on info line
       label               Border label (--border-label and --preview-label)
         preview-label     Border label of the preview window (--preview-label)
       prompt              Prompt
       pointer             Pointer to the current line
       marker              Multi-select marker
       spinner             Streaming input indicator
       header              Header
    """
    fg: str
    bg: str
    hl: str
    fg_plus: str
    bg_plus: str
    hl_plus: str
    info: str
    prompt_arrows: str
    # the pointer of hte current line
    pointer_current_line: str
    marker: str
    spinner: str
    header: str
    query: str

    def solarized(self):
        self.fg = "#2aa198"
        self.bg = "#002b36"
        self.hl = "#859900"
        self.fg_plus = "#6c71c4"
        self.bg_plus = "#002b36"
        self.hl_plus = "#268bd2"
        self.info = "#d33682"
        self.prompt_arrows = "#002b36"

        self.pointer_current_line = "#6c71c4"
        self.marker = "#268bd2"
        self.spinner = "#2aa198"
        self.header = "#268bd2"
        self.query = "#cb4b16"
        self.label = self.bg
        self.border = "#073642"

        return self





def hide_current_focused_window():
    """Used by fzf to hide the current focused window when pressing esc"""
    os.system(
        """osascript -e 'tell application "System Events" to keystroke "h" using {command down}'"""
    )


def main():
    import fire

    fire.Fire()


if __name__ == "__main__":
    main()
