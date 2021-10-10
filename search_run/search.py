from ddtrace import tracer

from search_run.search_ui.factory import UIFactory


class Search:
    """
    Opens search with all entries
    """

    @tracer.wrap("search_run.search.run")
    def run(self, cmd_get_rows):
        ui = UIFactory.get_instance()
        return ui.run(cmd_get_rows)
