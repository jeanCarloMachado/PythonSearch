from search_run.search_ui.fzf_in_terminal import FzfInTerminal


class Search:
    """
    Opens search with all entries
    """

    def __init__(self, configuration_exporter):
        self.configuration_exporter = configuration_exporter

    def run(self):
        return FzfInTerminal.build_search_ui().run()
