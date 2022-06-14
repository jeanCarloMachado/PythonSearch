

import os

class Mac:
    def __init__(self, configuration):
        self.configuration = configuration
        import os
        self.config_folder = f'{os.environ["HOME"]}/.config/iCanHazShortcut/'
    def generate(self):
        print("Generating macos shortctus")

        shortcut_found = False
        shortcut_number = 2
        os.system(f'cp {self.config_folder}/config.ini.part1 {self.config_folder}/config.ini')
        for key, content in list(self.configuration.commands.items()):
            if type(content) is dict and "mac_shortcut" in content:
                print(f"Generating shortcut for {key}")

                shortcut_content = self._entry(content['mac_shortcut'], key, shortcut_number)
                print(shortcut_content)
                with open(f"{self.config_folder}/config.ini", "a") as myfile:
                    myfile.write(shortcut_content)

                shortcut_number+=1
                shortcut_found = True

        if not shortcut_found:
            print("No shortcut found for mac" )

    def _entry(self, shortcut, key, number):
        return f"""
        
[shortcut{number}]
shortcut = {shortcut}
action = {key}
command = search_run run_key '{key}'
workdir = 
enabled = yes
"""
