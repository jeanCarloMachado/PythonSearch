from python_search.search_ui.fzf_terminal import FzfInTerminal


class Search:
    """
    Opens search with all entries
    """

    def __init__(self, configuration):
        self.configuration = configuration

    def run(self):
        return FzfInTerminal.build_search_ui(self.configuration).run()
