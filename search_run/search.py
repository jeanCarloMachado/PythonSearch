from ddtrace import tracer
from grimoire.event_sourcing.message import MessageBroker

from search_run.search_ui.factory import UIFactory


class Search:
    """
    Opens search with all entries
    """

    def __init__(self):
        self.message_passing = MessageBroker("run_key_command_performed")

    @tracer.wrap("search_run.search.run")
    def run(self, cmd_get_rows):
        ui = UIFactory.get_instance()
        return ui.run(cmd_get_rows)
