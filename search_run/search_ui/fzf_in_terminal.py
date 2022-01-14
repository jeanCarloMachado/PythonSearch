import os

from search_run.observability.logger import logger


class FzfInTerminal:
    """
    Renders the search ui using fzf + termite terminal
    """

    FONT_SIZE = 14
    PREVIEW_PERCENTAGE_SIZE = 50

    @staticmethod
    def build_search_ui():
        """ Assembles what is specific for the search ui exclusively"""
        preview_cmd = "echo {} | cut -d ':' -f1 --complement | jq . -C "
        return FzfInTerminal(height=300, width=1100, preview_cmd=preview_cmd)

    def __init__(self, *, height, width, preview_cmd):
        self.height = height
        self.width = width
        self.preview_cmd = preview_cmd

    def run(self) -> None:
        internal_cmd = f"""bash -c 'search_run ranking generate | \
        fzf \
        --cycle \
        --no-hscroll \
        --hscroll-off=0 \
        --bind "alt-enter:execute-silent:(nohup search_run run_key {{}} & disown)" \
        --bind "enter:execute-silent:(nohup search_run run_key {{}} & disown)" \
        --bind "enter:+execute-silent:(hide_launcher.sh)" \
        --bind "enter:+clear-query" \
        --bind "ctrl-l:clear-query" \
        --bind "ctrl-c:execute-silent:(nohup search_run clipboard_key {{}} & disown)" \
        --bind "ctrl-e:execute-silent:(nohup search_run edit_key {{}} & disown)" \
        --bind "ctrl-e:+execute-silent:(hide_launcher.sh)" \
        --bind "ctrl-k:execute-silent:(nohup search_run edit_key {{}} & disown)" \
        --bind "ctrl-k:+execute-silent:(sleep 0.2 ; hide_launcher.sh)" \
        --bind "esc:execute-silent:(hide_launcher.sh)" \
        --bind "ctrl-h:execute-silent:(hide_launcher.sh)" \
        --bind "ctrl-r:reload:(search_run ranking generate)" \
        --bind "ctrl-n:reload:(search_run nlp_ranking get_read_projection_rank_for_query {{q}})" \
        --bind "ctrl-t:execute-silent:(notify-send test)" \
        --bind "ctrl-q:execute-silent:(notify-send {{q}})" \
        --bind "ctrl-d:abort" \
        --preview "{self.preview_cmd}" \
        --preview-window=right,{FzfInTerminal.PREVIEW_PERCENTAGE_SIZE}%,wrap \
        --reverse -i --exact --no-sort'
        """

        self._launch_terminal(internal_cmd)

    def _launch_terminal(self, internal_cmd: str):

        launch_cmd = f"""ionice -n 3 nice -19 kitty \
        --title=launcher -o remember_window_size=n \
        -o initial_window_width={self.width}  \
        -o  initial_window_height={self.height} \
        -o font_size={FzfInTerminal.FONT_SIZE} \
         {internal_cmd}
        """
        logger.info(f"Command performed:\n {internal_cmd}")
        result = os.system(launch_cmd)
        if result != 0:
            raise Exception("Search run fzf projection failed")
