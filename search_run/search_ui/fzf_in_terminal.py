import os

from search_run.observability.logger import logger


class FzfInTerminal:
    """
    Renders the search ui using fzf + termite terminal
    """

    HEIGHT = 300
    WIDTH = 1100
    FONT_SIZE = 14
    PREVIEW_PERCENTAGE_SIZE = 50

    def __init__(self, title="Search and run: "):
        self.title = title

    def run(self, cmd: str) -> None:

        preview_cmd = "echo {} | cut -d \':\' -f1 --complement | jq . -C "

        internal_cmd = f"""bash -c '{cmd} | \
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
        --bind "ctrl-d:abort" \
        --bind "esc:execute-silent:(hide_launcher.sh)" \
        --bind "ctrl-h:execute-silent:(hide_launcher.sh)" \
        --bind "ctrl-r:reload:({cmd})" \
        --bind "ctrl-n:reload:(search_run nlp_ranking get_read_projection_rank_for_query {{q}})" \
        --bind "ctrl-t:execute-silent:(notify-send test)" \
        --bind "ctrl-q:execute-silent:(notify-send {{q}})" \
        --preview "{preview_cmd}" \
        --preview-window=right,{FzfInTerminal.PREVIEW_PERCENTAGE_SIZE}%,wrap \
        --reverse -i --exact --no-sort'
        """

        self._launch_terminal(internal_cmd)

    def _launch_terminal(self, internal_cmd):

        launch_cmd = f"""ionice -n 3 nice -19 kitty \
        --title=launcher -o remember_window_size=n \
        -o initial_window_width={FzfInTerminal.WIDTH}  \
        -o  initial_window_height={FzfInTerminal.HEIGHT} \
        -o font_size={FzfInTerminal.FONT_SIZE} \
         {internal_cmd}
        """
        logger.info(f"Command performed:\n {internal_cmd}")
        result = os.system(launch_cmd)
        if result != 0:
            raise Exception("Search run fzf projection failed")

