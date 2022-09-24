from __future__ import annotations

import inspect
import logging
import os


class EntriesGroup:
    """
    Main _configuration of the application. Customers are supposed to pass their own
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
        class_name_tag = self.__class__.__name__
        for key, command in self.commands.items():
            if type(command) is dict:
                if "tags" not in command:
                    command["tags"] = [class_name_tag]
                else:
                    if class_name_tag not in command["tags"]:
                        command["tags"].append(class_name_tag)

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
        @ deprecated use environment loader instead
        """

        from python_search.config import ConfigurationLoader

        return ConfigurationLoader().get_project_root()
