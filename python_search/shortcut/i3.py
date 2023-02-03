import logging
import os

from python_search.entries_group import EntriesGroup


class I3:
    """
    Setup a custom way of dealing with i3 shortcuts
    For this to work you have to rename your $HOME/.config/i3/config to $HOME/.config/i3/config_part 1
    And then let this script generate the file $HOME/.config/i3/config
    """

    def __init__(self, configuration: EntriesGroup):
        self.configuration = configuration

    def generate(self):

        shortcut_str = self._generate_i3_shortcuts_string()
        i3_config_path = os.path.join(os.environ["HOME"], ".config/i3")
        if not os.path.exists(f"{i3_config_path}/config_part1"):
            raise Exception("Cannot find part 1 of i3 _configuration")

        with open(f"{i3_config_path}/config_part2", "a") as myfile:
            myfile.write(shortcut_str)

        os.system(f"cat {i3_config_path}/config_part1 > {i3_config_path}/config")
        os.system(f"cat {i3_config_path}/config_part2 >> {i3_config_path}/config")

    def _generate_i3_shortcuts_string(self) -> str:
        """Generates a single string with all exported shortcuts"""
        result = "#automatically generated from now on\n"

        for key, content in list(self.configuration.commands.items()):
            if type(content) is dict and "i3_shortcut" in content:
                logging.info(f"Generating shortcut for {key}")
                identifier = self._generate_identifier(key)
                cmd = f'python_search run_key "{identifier}" --force_gui_mode=1 --from_shortcut=1'
                result = f"{result}bindsym {content['i3_shortcut']} exec {cmd}\n"

        return result

    def _generate_identifier(self, string):
        """
        strip the string from all special characters lefting only [A-B-09]
        """
        result = "".join(e for e in string if e.isalnum())
        result = result.lower()

        return result
