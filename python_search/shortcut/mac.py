import os
import time
import subprocess
import shutil
from typing import Optional

from python_search.search_ui.kitty import FzfInKitty


class Mac:
    """
    Mac support for tool iCanHazShortcut

    """

    START_SHORTCUT_NUMBER = 1

    def __init__(self, configuration):
        self.configuration = configuration
        import os

        self.config_folder = f'{os.environ["HOME"]}/.config/iCanHazShortcut/'

    def generate(self):
        print("Generating macos shortcuts")

        self._stop_app()

        shortcut_found = False

        BASE_CONFIG_LOCATION = os.environ.get(
            "BASE_CONFIG_LOCATION", self.config_folder
        )
        print("Base config location: ", BASE_CONFIG_LOCATION)

        shutil.copyfile(
            f"{BASE_CONFIG_LOCATION}/config.ini.part1",
            f"{self.config_folder}/config.ini",
        )

        content_to_write = ""

        content_to_write += self._add_shortcut(
            "⌃Space",
            "Launch python search",
            Mac.START_SHORTCUT_NUMBER,
            FzfInKitty.focus_kitty_command() + " || python_search_search launch",
        )
        Mac.START_SHORTCUT_NUMBER += 1

        for key, content in list(self.configuration.commands.items()):
            if not type(content) is dict:
                continue

            if "mac_shortcut" in content:
                shortcut_found = True
                content_to_write += self._add_shortcut(
                    content["mac_shortcut"], key, Mac.START_SHORTCUT_NUMBER
                )
                Mac.START_SHORTCUT_NUMBER += 1

            if "mac_shortcuts" in content:
                shortcut_found = True
                for shortcut in content["mac_shortcuts"]:
                    content_to_write += self._add_shortcut(
                        shortcut, key, Mac.START_SHORTCUT_NUMBER
                    )
                    Mac.START_SHORTCUT_NUMBER += 1

        if not shortcut_found:
            print("No shortcuts found for mac")
            return
        else:
            config_file = f"{self.config_folder}config.ini"
            with open(config_file, "a") as myfile:
                print(config_file, content_to_write)
                myfile.write(content_to_write)

        os.system(f"cd {self.config_folder} ; add_bom_to_file.sh config.ini")
        time.sleep(1)

        # restart shortcut app

        print("Restarting shortcut app")
        os.system("open -a iCanHazShortcut")

        print(f"Done! {Mac.START_SHORTCUT_NUMBER} shortcuts generated")

        number_of_items = subprocess.getoutput(
            f"grep '\[shortcut' {self.config_folder}config.ini | wc -l"
        )
        print(f"In the file we found {number_of_items} items")

    def _add_shortcut(
        self, shortcut: str, key: str, shortcut_number, custom_cmd: Optional[str] = None
    ) -> str:
        print(f"Generating shortcut for {key}")
        if custom_cmd is None:
            custom_cmd = f'run_key "{key}"'

        return f"""

[shortcut{shortcut_number}]
shortcut = {shortcut}
action = {key}{shortcut_number}
command = {custom_cmd} --from_shortcut True
workdir =
enabled = yes
"""

    def _stop_app(self):
        print("Killing shortcut app")

        get_pid_app = "pgrep iCanHazShortcut"

        try:
            output = subprocess.check_output(get_pid_app, shell=True, text=True)
        except Exception as e:
            print("Could not find PID! Restart will fail, try again.")
            return
        if len(output) < 3:
            print("Could not find PID! Restart will fail, try again.")
            return

        os.system("kill -9 " + output)
        time.sleep(3)
