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
        self.configuration = Configuration
        self.cached_file = Configuration.cached_filename

    @notify_execution()
    def recompute_rank(self, generate_shortcuts=True):
        """
            Recomputes the rank and saves the results on the file to be read
        """

        df = self.load_dataset()
        used_items = df['key'].tolist()
        items_dict = self.configuration().commands



        # linear decay for use
        #used_items = used_items[0:1000]
        total_used_items = len(used_items)
        scores_used_items = {}
        for position, key in enumerate(used_items):
            if key not in items_dict:
                continue

            score = (total_used_items - position) / total_used_items

            if key in scores_used_items:
                aggregation = score + (scores_used_items[key]  * (1/position))
                score = aggregation if aggregation < 1 else 1

            scores_used_items[key] = score
        sorted_used_items_score = sorted(scores_used_items, key=scores_used_items.get, reverse=True)



        #quadratic decay for position
        total_items = len(items_dict)
        natural_position_scored = {}
        for position, (key, value) in enumerate(items_dict.items()):

            natural_position_scored[key] = total_items / (total_items + position)

        sorted_natural_position_score = sorted(natural_position_scored, key=natural_position_scored.get, reverse=True)




        result = self.cyclical_placment(items_dict, sorted_used_items_score, sorted_natural_position_score)


        return self._export_to_file(result)

    def load_dataset(self):

        with open('/data/grimoire/message_topics/run_key_command_performed') as f:
            data = []
            for line in f.readlines():
                try:
                    data.append(json.loads(line))
                except Exception as e:
                    print(f"Line broken: {line}")
        df = pd.DataFrame(data)

        # revert the list (latest on top)
        df = df.iloc[::-1]

        return df


    def cyclical_placment(self, items_dict, sorted_used_items_score, sorted_natural_position_score):
        result = []
        used_keys = []
        total_items = len(items_dict)
        position =0
        while len(sorted_natural_position_score) > 0:

            if position % 2 == 0 and len(sorted_used_items_score) > 0:
                key = sorted_used_items_score.pop(0)
            else:
                key = sorted_natural_position_score.pop(0)

            if key in used_keys:
                continue

            result.append((key, items_dict[key]))
            used_keys.append(key)
            position = position + 1

        return result


    def _export_to_file(self, data):
        fzf_lines = ""
        for name, content in data:
            fzf_lines += f"{name.lower()}: {content}\n"

        write_file(self.configuration.cached_filename, fzf_lines)



