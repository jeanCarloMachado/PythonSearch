import logging

from search_run.terminal import Terminal


class Shortcut:
    def reset(self):
        """ reset existing shortcuts, necesary only for gnome"""
        Terminal.run_command(
            "gsettings reset-recursively org.gnome.settings-daemon.plugins.media-keys"
        )

    def register(self, cmd, shortcut):
        name = self._generate_identifier(cmd)
        shortcut_cmd = f'set_custom_shortcut.py "{name}" "{cmd}" "{shortcut}"'
        logging.info(f"Register shortcut command: {shortcut_cmd}")
        Terminal.run_command(shortcut_cmd)

    def _generate_identifier(string):
        """
        strip the string from all special characters lefting only [A-B-09]
        """
        result = "".join(e for e in string if e.isalnum())
        result = result.lower()

        return result
