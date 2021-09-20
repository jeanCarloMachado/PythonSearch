class BaseConfiguration:
    """
    Main configuration of the application. Customers are supposed to pass their own
    """

    # the location of the dumped index
    cached_filename: str = "/tmp/search_and_run_configuration_cached"
    commands: dict = {}

    def __init__(self):
        pass

    def get_command(self, given_key):
        """ Returns command value based on the key name, must match 11"""
        given_key = given_key.lower()
        for key, value in self.commands.items():
            if key.lower() == given_key:
                return value

        raise Exception(f"Value not found for key: {given_key}")

    def get_keys(self):
        keys = []
        for key, value in self.commands.items():
            keys.append(key)

        return keys

    def get_hydrated_commands(self):
        result = {}

        for key, command in self.commands.items():
            if type(command) is dict:
                if not "tags" in command:
                    command["tags"] = [self.__class__.__name__]
                else:
                    command["tags"].append(self.__class__.__name__)

            result[key] = command

        return result

    def aggregate_commands(self, commands_classes):
        for class_i in commands_classes:
            instance = class_i()

            if issubclass(class_i, BaseConfiguration):
                cmd_items = instance.get_hydrated_commands()
            else:
                cmd_items = instance.commands

            self.commands = {**self.commands, **cmd_items}

    def get_cached_filename(self):
        return self.cached_filename
