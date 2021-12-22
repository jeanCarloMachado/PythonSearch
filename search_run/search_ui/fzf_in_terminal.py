import os

from search_run.observability.logger import logger


class FzfInTerminal:
    """
    Renders the search ui using fzf + termite terminal
    """

    HEIGHT = 300
    WIDTH = 1100

    def __init__(self, title="Search and run: "):
        self.title = title

    def run(self, cmd: str) -> None:

        internal_command = f""" bash -c '{cmd} | \
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
        --preview "echo {{}} | cut -d \':\' -f1 --complement | jq . -C " \
        --preview-window=right,60%,wrap \
        --reverse -i --exact --no-sort'
        """

        launch_cmd = f"""ionice -n 3 nice -19 kitty \
        --title=launcher -o remember_window_size=n \
        -o initial_window_width={FzfInTerminal.WIDTH}  \
        -o  initial_window_height={FzfInTerminal.HEIGHT} \
        -o font_size=12 \
         {internal_command}
        """
        logger.info(f"Command performed:\n {internal_command}")
        result = os.system(launch_cmd)
        if result != 0:
            raise Exception("Search run fzf projection failed")
