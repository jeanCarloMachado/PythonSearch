import re
from ddtrace import tracer

from grimoire.event_sourcing.message import MessageBroker
from search_run.entities import SearchResult
from search_run.search_ui.factory import UIFactory
from search_run.context import Context
from search_run.interpreter.main import Interpreter
from search_run.events import SearchPerformed


class Search:
    """
    Opens dmenu, gets a string and interprets it
    """
    def __init__(self):
        self.message_passing = MessageBroker("run_key_command_performed")


    def run(self, cmd_get_rows):

        result = self._select_option(cmd_get_rows)

        if not result.result:
            print("No content, returning")
            return


        event = SearchPerformed(key=self.get_key(result.result), given_input=result.query)
        self.message_passing.produce(event.__dict__)

        Context.get_instance().enable_gui_mode()
        Interpreter.build_instance().default(result.result)


    @tracer.wrap("render_dmenu_options")
    def _select_option(self, cmd_get_rows) -> SearchResult:
        ui = UIFactory.get_instance()
        return ui.run(cmd_get_rows)

    def get_key(self, given_input):
        """
        @todo move this code to a centalized place
        :param given_input:
        :return:
        """
        key_value = re.compile("([A-Za-z0-9 _-]+): (.*)")
        matches_kv = key_value.search(given_input)
        key = given_input
        if matches_kv:
            key = matches_kv.group(1)
        return key
