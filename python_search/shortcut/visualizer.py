
from python_search.configuration.loader import ConfigurationLoader


class ShortcutsVisualizer:
    def __init__(self):
        self.configuration = ConfigurationLoader().get_config_instance()
    def generate(self):
        shortcuts_to_keys = []

        for key, content in list(self.configuration.commands.items()):
            if not isinstance(content, dict):
                continue

            if "mac_shortcut" in content:
                shortcuts_to_keys.append((content['mac_shortcut'], key))
            
            if 'mac_shortcuts' in content:
                for shortcut in content['mac_shortcuts']:
                    shortcuts_to_keys.append((shortcut, key))
        # sort         
        
        shortcuts_to_keys = sorted(shortcuts_to_keys, key=lambda the_tuple: self.get_only_alnum(the_tuple[0]),reverse=False)

        result = []
        counter = 1
        for shortcut, key in shortcuts_to_keys:
            result.append(f"{counter}. {shortcut} - {key}")
            counter += 1


        return result

    def get_only_alnum(self, string):
        result = [x for x in string if string.isalnum() ]
        result = "".join(result)
        return result


def main():
    import fire
    fire.Fire(ShortcutsVisualizer)


if __name__ == "__main__":
    import fire
    fire.Fire(ShortcutsVisualizer)