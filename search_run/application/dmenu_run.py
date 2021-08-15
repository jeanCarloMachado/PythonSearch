from ddtrace import tracer

from grimoire.desktop.dmenu import Dmenu
from search_run.domain.context import Context
from search_run.domain.interpreter.main import Interpreter
from grimoire.event_sourcing.message import MessageBroker


class DmenuRun:
    """
    Main entry point of the application
    Opens dmenu, gets a string and interprets it

    """
    # @todo manage to get the rows from inside this application rather than having it passed
    def run(self, cmd_get_rows):
        @tracer.wrap("render_dmenu_options")
        def select_option():
            ui = Dmenu(title="Search run:")
            return ui.rofi(cmd_get_rows)

        text_input = select_option()

        if not text_input:
            print("No content, returning")
            return

        Context.get_instance().enable_gui_mode()


        Interpreter.build_instance().default(text_input)
