import os
import time


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
        print("Generating macos shortctus")

        self._stop_app()

        shortcut_found = False
        # starts with number 2 as number 1 is static in config.part1

        import shutil

        shutil.copyfile(
            f"{self.config_folder}/config.ini.part1", f"{self.config_folder}/config.ini"
        )

        content_to_write = ""
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

        print(f"Done! {Mac.START_SHORTCUT_NUMBER}  shortcuts generated")

        import subprocess

        number_of_items = subprocess.getoutput(
            f"grep '\[shortcut' {self.config_folder}config.ini | wc -l"
        )
        print(f"In the file we found {number_of_items} items")

    def _add_shortcut(self, shortcut: str, key: str, shortcut_number) -> str:
        print(f"Generating shortcut for {key}")
        return self._entry(shortcut, key, shortcut_number)

    def _stop_app(self):
        print("Killing shortcut app")
        from subprocess import PIPE, Popen

        get_pid_app = "pgrep iCanHazShortcut"
        import subprocess;
        output = subprocess.check_output(get_pid_app, shell=True, text=True)
        if len(output) < 3:
            raise Exception("Could not find PID! Restart will fail, try again.")

        os.system("kill -9 " + output)
        time.sleep(3)

    def _entry(self, shortcut, key, number) -> str:
        HOME = os.environ["HOME"]
        shortcut = shortcut
        # @todo make the first shortcut system independent
        return f"""

[shortcut{number}]
shortcut = {shortcut}
action = {key}{number}
command =  run_key "{key}" --from_shortcut True
workdir =
enabled = yes
"""
