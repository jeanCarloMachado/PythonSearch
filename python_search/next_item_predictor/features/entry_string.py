from python_search.configuration.loader import ConfigurationLoader


class EntryString:
    def __init__(self):
        self.configuration = ConfigurationLoader().load_config()

    def get_key_string(self, key: str) -> str:
        """
        Gets the string representation of the key
        """
        if key not in self.configuration.commands.keys():
            return key

        return f"{key} {self.configuration.commands[key]}"
