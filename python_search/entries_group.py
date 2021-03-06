from __future__ import annotations

import inspect
import os


class EntriesGroup:
    """
    Main configuration of the application. Customers are supposed to pass their own
    """

    # the location of the dumped index
    commands: dict = {}

    def aggregate_commands(self, commands_classes):
        """
        aggregates a list of classes or instances
        """
        for class_i in commands_classes:
            is_class = inspect.isclass(class_i)
            instance = class_i() if is_class else class_i

            if isinstance(instance, EntriesGroup):
                cmd_items = instance.get_hydrated_commands()
            else:
                cmd_items = instance.commands

            self.commands = {**self.commands, **cmd_items}

    def get_command(self, given_key):
        """Returns command value based on the key name, must match 11"""
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
                if "tags" not in command:
                    command["tags"] = [self.__class__.__name__]
                else:
                    command["tags"].append(self.__class__.__name__)

            result[key] = command

        return result

    def get_source_file(self):
        """
        Returns the path of the source code where the config is stored
        """
        import sys

        return sys.argv[0]

    def get_project_root(self):
        """
        Returns the root of the project where the config is
        @todo substitues PROJECT_ROOT with this
        """

        return os.environ["PS_ENTRIES_HOME"]
