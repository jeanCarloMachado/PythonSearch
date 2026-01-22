import json
import os

from python_search.host_system.system_paths import SystemPaths


class MacKarabinerElements:
    def __init__(self, configuration):
        home = os.environ.get("HOME")
        self.BASE_KARABINER_ELEMENTS_FILE = f"{SystemPaths.PYTHON_SEARCH_PATH}/karabiner_base.json"
        self.MAIN_KARABINER_ELEMENTS_FILE = f"{home}/.config/karabiner/karabiner.json"
        self.configuration = configuration

    def generate(self):
        # read json base file
        with open(self.BASE_KARABINER_ELEMENTS_FILE, "r") as file:
            karabiner_content = json.load(file)

        for key, content in list(self.configuration.commands.items()):
            if not isinstance(content, dict):
                continue

            if "mac_shortcut" in content:
                karabiner_content["profiles"][0]["complex_modifications"]["rules"].append(
                    self.parse_mac_shortcut(content["mac_shortcut"], content, key)
                )

            if "mac_shortcuts" in content:
                for shortcut in content["mac_shortcuts"]:
                    karabiner_content["profiles"][0]["complex_modifications"]["rules"].append(
                        self.parse_mac_shortcut(shortcut, content, key)
                    )

        # write the new content to the main file
        with open(self.MAIN_KARABINER_ELEMENTS_FILE, "w") as file:
            json.dump(karabiner_content, file, indent=4)
            print(f"Karabiner elements file {self.MAIN_KARABINER_ELEMENTS_FILE} updated")

    def parse_mac_shortcut(self, shortcut: str, content: dict, key: str):
        """
        Shortcut:
        is the expression that maps the shortcut
        example: "⌘⇧t"

        """
        run_key_binary = SystemPaths.get_binary_full_path("run_key")
        shell_command = f"/opt/miniconda3/condabin/conda run -n python313 {run_key_binary} '{key}'"
        print("Processing shortcut: ", shortcut, " for key: ", key, " with shell command: ", shell_command)
        shortcut_dict = {}
        shortcut_dict["description"] = f"RUN {key} with shortcut {shortcut}"
        shortcut_dict["manipulators"] = [{"from": {}, "to": [{"shell_command": shell_command}], "type": "basic"}]

        if shortcut == "right_gui":
            shortcut_dict["manipulators"][0]["from"]["key_code"] = "right_gui"
            return shortcut_dict
        if shortcut == "right_gui_shift":
            shortcut_dict["manipulators"][0]["from"]["key_code"] = "right_gui"
            shortcut_dict["manipulators"][0]["from"]["modifiers"] = {"mandatory": ["left_shift"]}
            return shortcut_dict

        if shortcut == "right_alt":
            shortcut_dict["manipulators"][0]["from"]["key_code"] = "right_alt"
            return shortcut_dict

        if "return_or_enter" in shortcut:
            shortcut_dict["manipulators"][0]["from"]["key_code"] = "return_or_enter"

        for character in shortcut:
            if character == "⌘":
                if "modifiers" not in shortcut_dict["manipulators"][0]["from"]:
                    shortcut_dict["manipulators"][0]["from"]["modifiers"] = {"mandatory": ["left_gui"]}
                else:
                    shortcut_dict["manipulators"][0]["from"]["modifiers"]["mandatory"].append("left_gui")
            elif character == "⇧":
                if "modifiers" not in shortcut_dict["manipulators"][0]["from"]:
                    shortcut_dict["manipulators"][0]["from"]["modifiers"] = {"mandatory": ["left_shift"]}
                else:
                    shortcut_dict["manipulators"][0]["from"]["modifiers"]["mandatory"].append("left_shift")
            elif character == "⌥":
                if "modifiers" not in shortcut_dict["manipulators"][0]["from"]:
                    shortcut_dict["manipulators"][0]["from"]["modifiers"] = {"mandatory": ["left_alt"]}
                else:
                    shortcut_dict["manipulators"][0]["from"]["modifiers"]["mandatory"].append("left_alt")
            elif character == "⌃":
                if "modifiers" not in shortcut_dict["manipulators"][0]["from"]:
                    shortcut_dict["manipulators"][0]["from"]["modifiers"] = {"mandatory": ["left_control"]}
                else:
                    shortcut_dict["manipulators"][0]["from"]["modifiers"]["mandatory"].append("left_control")

            # test if is alphanumeric
            if character.isalnum():
                # make it lowercase
                character = character.lower()
                shortcut_dict["manipulators"][0]["from"]["key_code"] = character

        return shortcut_dict
