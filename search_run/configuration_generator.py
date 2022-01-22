import logging
import os

from grimoire.file import write_file
from grimoire.shell import shell
from grimoire.string import generate_identifier

from search_run.base_configuration import EntriesGroup
from search_run.shortcut.register import Shortcut


class ConfigurationGenerator:
    """
    Responsible to apply all the side-effects of search-run entries
    Called when we change search run or want to initailze it in the system.

    Responsibilities include:
    - generate shortcuts
    - Generate new  read centric ranking projection
    """

    def __init__(self, configuration: EntriesGroup):
        self.configuration = configuration
        self.shortcut = Shortcut()
        self.generate_shortcuts = True

    def export(
        self,
        generate_shortcuts=True,
    ):
        """
        Export a new configuration.

        You can customize the method of ranking.
        By default the ranking is just a projection of the data.
        But if you want to have better ranking you can pass "complete"
        the more expensive algorithm optimizing the ranking will be used.
        """

        self.generate_shortcuts = generate_shortcuts
        self._generate_i3_shortcuts()

    def _generate_i3_shortcuts(self):
        if not self.generate_shortcuts:
            return
        shortcut_str = self._generate_i3_shortcuts_string()

        i3_config_path = "/home/jean/.config/i3"
        if not os.path.exists(f"{i3_config_path}/config_part1"):
            raise Exception("Cannot find part 1 of i3 configuration")

        write_file(f"{i3_config_path}/config_part2", shortcut_str)

        shell.run(f"cat {i3_config_path}/config_part1 > {i3_config_path}/config")
        shell.run(f"cat {i3_config_path}/config_part2 >> {i3_config_path}/config")

    def _generate_i3_shortcuts_string(self) -> str:
        """Generates a single string with all exported shortcuts """
        result = "#automatically generated from now on\n"

        for key, content in list(self.configuration.commands.items()):
            if type(content) is dict and "i3_shortcut" in content:
                logging.info(f"Generating shortcut for {key}")
                identifier = generate_identifier(key)
                cmd = f'search_run run_key "{identifier}" --force_gui_mode=1 --from_shortcut=1'
                result = f"{result}bindsym {content['i3_shortcut']} exec {cmd}\n"

        return result
