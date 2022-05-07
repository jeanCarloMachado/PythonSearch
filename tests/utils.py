from search_run.entries_group import EntriesGroup


def build_config(given_commands):
    class Configuration(EntriesGroup):
        commands = given_commands

    return Configuration()
