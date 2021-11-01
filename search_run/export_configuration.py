import logging
import os

from grimoire.decorators import notify_execution
from grimoire.desktop.shortcut import Shortcut
from grimoire.file import file_exists, write_file
from grimoire.shell import shell
from grimoire.string import generate_identifier

from search_run.configuration import BaseConfiguration
from search_run.ranking.ranking import Ranking


class ConfigurationExporter:
    """
    Write to the file all the commands and generates shortcuts
    """

    def __init__(self, configuration: BaseConfiguration):
        self.configuration = configuration
        self.shortcut = Shortcut()
        self.generate_shortcuts = True

    def generate_and_get_cached_file_name(self):
        """singleton kind of method, will not initalize the configuration if it is already in cache"""
        if not file_exists(self.configuration.get_cached_filename()):
            self.export()

        return self.configuration.get_cached_filename()

    @notify_execution()
    def export(self, generate_shortcuts=True, ignore_lock=False):

        lock_file_name = "/tmp/search_run_export.lock"

        if file_exists(lock_file_name) and not ignore_lock:
            raise Exception("Export currently in progress will not start a new one")
        else:
            os.system(f"touch {lock_file_name}")

        self.generate_shortcuts = generate_shortcuts

        logging.info(f"Writing to file: {self.configuration.get_cached_filename()}")
        Ranking().recompute_rank()
        self._generate_i3_shortcuts()

        os.system(f"rm {lock_file_name}")

        return self.configuration.get_cached_filename()

    @notify_execution()
    def _generate_i3_shortcuts(self):
        if not self.generate_shortcuts:
            return
        result = self._generate_i3_shortcuts_string()

        i3_config_path = "/home/jean/.config/i3"
        if not file_exists(f"{i3_config_path}/config_part1"):
            raise Exception("Cannot find part 1 of i3 configuration")

        write_file(f"{i3_config_path}/config_part2", result)

        shell.run(f"cat {i3_config_path}/config_part1 > {i3_config_path}/config")
        shell.run(f"cat {i3_config_path}/config_part2 >> {i3_config_path}/config")

    def _generate_i3_shortcuts_string(self):
        result = "#automatically generated from now on\n"

        for name, content in list(self.configuration.commands.items()):
            if type(content) is dict and "i3_shortcut" in content:
                identifier = generate_identifier(name)
                cmd = f'search_run run_key "{identifier}" --force_gui_mode=1 --from_shortcut=1'
                result = f"{result}bindsym {content['i3_shortcut']} exec {cmd}\n"

        return result
