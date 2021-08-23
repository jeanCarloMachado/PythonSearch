from ddtrace import tracer

from grimoire.desktop.dmenu import Dmenu
from search_run.context import Context
from search_run.interpreter.main import Interpreter


class DmenuRun:
    """
    Opens dmenu, gets a string and interprets it

    """

    def run(self, cmd_get_rows):

        text_input = self._select_option(cmd_get_rows)

        if not text_input:
            print("No content, returning")
            return

        Context.get_instance().enable_gui_mode()
        Interpreter.build_instance().default(text_input)


    @tracer.wrap("render_dmenu_options")
    def _select_option(self, cmd_get_rows):
        ui = Dmenu(title="Search run:")
        return ui.rofi(cmd_get_rows)
