import logging

from grimoire.decorators import notify_execution
from grimoire.desktop.shortcut import Shortcut
from grimoire.file import file_exists, write_file
from grimoire.shell import shell
from search_run.configuration import BaseConfiguration
from grimoire.string import generate_identifier
from search_run.ranking.ranking import Ranking


class ConfigurationExporter:
    """
    Write to the file all the commands and generates shortcuts
    """

    def __init__(self, configuration: BaseConfiguration):
        self.configuration = configuration
        self.shortcut = Shortcut()
        self.generate_shortcuts = True

    @notify_execution()
    def export(self, generate_shortcuts=True):
        self.generate_shortcuts = generate_shortcuts
        self._write_to_file()

    def get_cached_file_name(self):
        """singleton kind of method, will not initalize the configuration if it is already in cache"""
        if not file_exists(self.configuration.get_cached_filename()):
            self._write_to_file()

        return self.configuration.get_cached_filename()

    def _write_to_file(self):
        """
        @todo cache this function
        """
        logging.info(f"Writing to file: {self.configuration.get_cached_filename()}")
        Ranking().recompute_rank()
        # self.generate_gnome_shortcuts()
        self.generate_i3_shortcuts()

        return self.configuration.get_cached_filename()

    @notify_execution()
    def generate_i3_shortcuts(self):
        if not self.generate_shortcuts:
            return
        result = self.generate_i3_shortcuts_string()

        i3_config_path = "/home/jean/.config/i3"
        if not file_exists(f"{i3_config_path}/config_part1"):
            raise Exception("Cannot find part 1 of i3 configuration")

        write_file(f"{i3_config_path}/config_part2", result)

        shell.run(f"cat {i3_config_path}/config_part1 > {i3_config_path}/config")
        shell.run(f"cat {i3_config_path}/config_part2 >> {i3_config_path}/config")

    def generate_i3_shortcuts_string(self):
        result = "#automatically generated from now on\n"

        for name, content in list(self.configuration.commands.items()):
            if type(content) is dict and "i3_shortcut" in content:
                identifier = generate_identifier(name)
                cmd = f'search_run run_key "{identifier}" --force_gui_mode=1 --from_shortcut=1'
                result = f"{result}bindsym {content['i3_shortcut']} exec {cmd}\n"

        return result

    def generate_gnome_shortcuts(self):
        if not self.generate_shortcuts:
            return

        self.shortcut.reset()
        for name, content in list(self.configuration.commands.items()):
            if type(content) is dict and "shortcut" in content:
                identifier = generate_identifier(name)
                self.shortcut.register(
                    f'search_run run_key "{identifier}" --force_gui_mode=1',
                    content["shortcut"],
                )

    def export_configuration_to_file(self):
        fzf_lines = ""
        for name, content in list(self.configuration.commands.items()):
            fzf_lines += f"{name.lower()}: {content}\n"

        write_file(self.configuration.get_cached_filename(), fzf_lines)
