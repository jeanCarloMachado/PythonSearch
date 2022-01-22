from search_run.base_configuration import EntriesGroup


def build_config(given_commands):
    class Configuration(EntriesGroup):
        commands = given_commands

    return Configuration()
