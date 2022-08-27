#!/usr/bin/env python3
import logging
import subprocess

from python_search.entries_group import EntriesGroup


class Gnome:
    def __init__(self, configuration: EntriesGroup):
        self.configuration = configuration

    def generate(self):
        print("Generating gnome shortctus")
        self._reset()

        shortcut_found = False
        for key, content in list(self.configuration.commands.items()):
            if type(content) is dict and "gnome_shortcut" in content:
                logging.info(f"Generating shortcut for {key}")
                identifier = self._generate_identifier(key)
                cmd = f'python_search run_key "{identifier}" --force_gui_mode=1 --from_shortcut=1'
                self.generate_shortcut(identifier, cmd, content["gnome_shortcut"])
                shortcut_found = True

        if not shortcut_found:
            print("No shorcut found for gnome")

    def _reset(self):
        """reset existing shortcuts, necessary only for gnome"""

        from python_search.interpreter.cmd import CmdInterpreter

        CmdInterpreter(
            {
                "cmd": "gsettings reset-recursively org.gnome.settings-daemon.plugins.media-keys"
            }
        )

    def generate_shortcut(self, name: str, command: str, binding: str):
        """
        Super key:                 <Super>
        Control key:               <Primary> or <Control>
        Alt key:                   <Alt>
        Shift key:                 <Shift>
        numbers:                   1 (just the number)
        Spacebar:                  space
        Slash key:                 slash
        Asterisk key:              asterisk (so it would need `<Shift>` as well)
        Ampersand key:             ampersand (so it would need <Shift> as well)

        a few numpad keys:
        Numpad divide key (`/`):   KP_Divide
        Numpad multiply (Asterisk):KP_Multiply
        Numpad number key(s):      KP_1
        Numpad `-`:                KP_Subtract
        """

        # defining keys & strings to be used
        key = "org.gnome.settings-daemon.plugins.media-keys custom-keybindings"
        subkey1 = key.replace(" ", ".")[:-1] + ":"
        item_s = "/" + key.replace(" ", "/").replace(".", "/") + "/"
        firstname = "custom"
        # get the current list of custom shortcuts
        get = lambda cmd: subprocess.check_output(["/bin/bash", "-c", cmd]).decode(
            "utf-8"
        )
        array_str = get("gsettings get " + key)
        # in case the array was empty, remove the annotation hints
        command_result = array_str.lstrip("@as")
        current = eval(command_result)
        # make sure the additional keybinding mention is no duplicate
        n = 1
        while True:
            new = item_s + firstname + str(n) + "/"
            if new in current:
                n = n + 1
            else:
                break
        # add the new keybinding to the list
        current.append(new)
        # create the shortcut, set the name, command and shortcut key
        cmd0 = "gsettings set " + key + ' "' + str(current) + '"'
        cmd1 = "gsettings set " + subkey1 + new + " name '" + name + "'"
        cmd2 = "gsettings set " + subkey1 + new + " command '" + command + "'"
        cmd3 = "gsettings set " + subkey1 + new + " binding '" + binding + "'"

        for cmd in [cmd0, cmd1, cmd2, cmd3]:
            print(f"CMD executing: {cmd}")
            subprocess.call(["/bin/bash", "-c", cmd])

    def _generate_identifier(self, string):
        """
        strip the string from all special characters lefting only [A-B-09]
        """
        result = "".join(e for e in string if e.isalnum())
        result = result.lower()

        return result
