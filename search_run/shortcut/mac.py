


class Mac:
    def __init__(self, configuration):
        self.configuration = configuration
    def generate(self):
        print("Generating macos shortctus")

        shortcut_found = False
        for key, content in list(self.configuration.commands.items()):
            if type(content) is dict and "mac_shortcut" in content:
                print(f"Generating shortcut for {key}")
                shortcut_found = True

        if not shortcut_found:
            print("No shortcut found for mac" )

