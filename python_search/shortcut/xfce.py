import os


class XFCE:
    def __init__(self, configuration):
        self.configuration = configuration

    def generate(self):
        print("Generating XFCE-Shortcuts")
        os.system(
            "xfconf-query -c xfce4-keyboard-shortcuts -p '/commands/custom/<Super>r' -n -t string -s firefox"
        )

        for key, content in list(self.configuration.commands.items()):
            if not type(content) is dict:
                continue

            if "xfce_shortcut" in content:
                command = f"""xfconf-query -c xfce4-keyboard-shortcuts -p '/commands/custom/{content['xfce_shortcut']}' -n -t string -s 'run_key "{key}"' """
                print(command)
                os.system(command)
