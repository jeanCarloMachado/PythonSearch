from search_run.search_ui.fzf_in_terminal import FzfInTerminal


class Search:
    """
    Opens search with all entries
    """

    def run(self):
        return FzfInTerminal.build_search_ui().run()
