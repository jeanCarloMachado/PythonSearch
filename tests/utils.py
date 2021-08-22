from search_run.configuration import BaseConfiguration


def build_config(given_commands):
    class Configuration(BaseConfiguration):
        commands = given_commands

    return Configuration()
