

import os

class Mac:
    """
    Mac support for tool iCanHazShortcut

    """
    def __init__(self, configuration):
        self.configuration = configuration
        import os
        self.config_folder = f'{os.environ["HOME"]}/.config/iCanHazShortcut/'

    def generate(self):
        print("Generating macos shortctus")

        shortcut_found = False
        # starts with number 2 as number 1 is static in config.part1
        shortcut_number = 2
        import shutil
        shutil.copyfile(f'{self.config_folder}/config.ini.part1', f'{self.config_folder}/config.ini')

        for key, content in list(self.configuration.commands.items()):
            if type(content) is dict and "mac_shortcut" in content:
                print(f"Generating shortcut for {key}")

                shortcut_content = self._entry(content['mac_shortcut'], key, shortcut_number)
                with open(f"{self.config_folder}/config.ini", "a") as myfile:
                    print(shortcut_content)
                    myfile.write(shortcut_content)

                shortcut_number+=1
                shortcut_found = True

        if not shortcut_found:
            print("No shortcut found for mac" )
            return

        os.system(f"cd {self.config_folder} ; add_bom_to_file.sh config.ini")

        os.system('pkill -f iCanHaz')
        os.system('open -a iCanHazSHortcut')

    def _entry(self, shortcut, key, number):
        shortcut = shortcut
        return f"""
        
[shortcut{number}]
shortcut = {shortcut}
action = {key}
command = log_command.sh search_run run_key '{key}'
workdir = 
enabled = yes
"""
