import json
import os

from python_search.host_system.system_paths import SystemPaths


class MacKarabinerElements:
    SPECIAL_KEY_ALIASES = {
        "↩": "return_or_enter",
        "⏎": "return_or_enter",
        "⌤": "return_or_enter",
    }

    def __init__(self, configuration):
        home = os.environ.get("HOME")
        self.BASE_KARABINER_ELEMENTS_FILE = f"{SystemPaths.PYTHON_SEARCH_PATH}/karabiner_base.json"
        self.MAIN_KARABINER_ELEMENTS_FILE = f"{home}/.config/karabiner/karabiner.json"
        self.configuration = configuration

    def generate(self):
        # read json base file
        with open(self.BASE_KARABINER_ELEMENTS_FILE, "r") as file:
            raw = file.read()

        python_search_binary = SystemPaths.get_binary_full_path("python_search")
        raw = raw.replace("/opt/miniconda3/envs/python313/bin/python_search", python_search_binary)
        run_key_binary = SystemPaths.get_binary_full_path("run_key")
        raw = raw.replace("/opt/miniconda3/envs/python313/bin/run_key", run_key_binary)
        # Caps Lock opens the native Rust launcher, which lives outside the Python env.
        raw = raw.replace("__PS_UI__", MacKarabinerElements.ps_ui_binary())
        karabiner_content = json.loads(raw)

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
        shell_command = f"{run_key_binary} '{key}'"
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

        normalized_shortcut = shortcut
        for alias, key_code in self.SPECIAL_KEY_ALIASES.items():
            if alias in normalized_shortcut:
                normalized_shortcut = normalized_shortcut.replace(alias, key_code)

        if "return_or_enter" in normalized_shortcut:
            shortcut_dict["manipulators"][0]["from"]["key_code"] = "return_or_enter"
            normalized_shortcut = normalized_shortcut.replace("return_or_enter", "")

        for character in normalized_shortcut:
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

    @staticmethod
    def ps_ui_binary() -> str:
        """
        Absolute path to the native launcher.

        Karabiner runs shell commands with a minimal PATH, so the binary has to be named in full.
        """
        import os
        import shutil

        candidates = [
            os.environ.get("PS_UI_BINARY"),
            os.path.expanduser("~/.local/bin/ps_ui"),
            shutil.which("ps_ui"),
        ]
        for candidate in candidates:
            if candidate and os.path.exists(candidate):
                return candidate

        raise Exception(
            "Could not find the ps_ui binary. Build and install it with "
            "PythonSearch/rust/install.sh, or set PS_UI_BINARY."
        )
