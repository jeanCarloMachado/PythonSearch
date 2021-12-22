from ddtrace import tracer

from search_run.search_ui.fzf_in_terminal import FzfInTerminal


class Search:
    """
    Opens search with all entries
    """

    def __init__(self, configuration_exporter):
        self.configuration_exporter = configuration_exporter

    @tracer.wrap("search_run.search.run")
    def run(self):

        """returns the shell command to perform to get all get_options_cmd
        and generates the side-effect of createing a new cache file if it does not exist"""
        configuration_file_name = (
            self.configuration_exporter.generate_and_get_cached_file_name()
        )
        cmd = f'cat "{configuration_file_name}" '

        return FzfInTerminal().run(cmd)
