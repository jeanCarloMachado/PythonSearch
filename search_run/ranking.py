import logging

from grimoire.decorators import notify_execution
from grimoire.desktop.shortcut import Shortcut
from grimoire.file import file_exists, write_file
from grimoire.search_run.search_run_config import Configuration
from grimoire.shell import shell
from grimoire.string import generate_identifier
import pandas as pd
import json


class Ranking:
    """
    Write to the file all the commands and generates shortcuts
    """

    def __init__(self):
        self.configuration = Configuration()
        self.cached_file = Configuration.cached_filename

    @notify_execution()
    def recompute_rank(self, generate_shortcuts=True):
        with open('/data/grimoire/message_topics/run_key_command_performed') as f:
            data = []
            for line in f.readlines():
                try:
                    data.append(json.loads(line))
                except Exception as e:
                    print(f"Line broken: {line}")
            df = pd.DataFrame(data)
            df = df.iloc[::-1]
            last_active_keys = df['key'].drop_duplicates().head(50).tolist()


        items_dict = self.configuration.commands
        last_active_items = [(i, items_dict[i]) for i in last_active_keys if i in items_dict]

        for key in last_active_keys:
            if key in items_dict:
                del items_dict[key]

        data = last_active_items + list(items_dict.items())

        return self.export_configuration_to_file(data)

    def export_configuration_to_file(self, data):
        fzf_lines = ""
        for name, content in data:
            fzf_lines += f"{name.lower()}: {content}\n"

        write_file(self.configuration.cached_filename, fzf_lines)



