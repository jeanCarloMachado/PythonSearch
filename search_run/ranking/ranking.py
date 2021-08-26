from grimoire.decorators import notify_execution
from grimoire.file import write_file
from grimoire.search_run.search_run_config import Configuration
import pandas as pd
import json

from search_run.logger import configure_logger

logger = configure_logger()


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

        entries: dict = self.configuration().commands
        commands_performed = self.load_commands_performed_df()

        result = self.cyclical_placment(entries, commands_performed)

        return self._export_to_file(result)

    def cyclical_placment(self, entries, commands_performed):
        """Put 1 result of natural rank after 1 result of visits"""

        used_items = self.compute_used_items_score(entries, commands_performed)
        natural_position = self.compute_natural_position_scores(entries)

        result = []
        used_keys = []
        total_items = len(entries)
        position = 0
        while len(natural_position) > 0:

            if position % 2 == 0 and len(used_items) > 0:
                key = used_items.pop(0)
            else:
                key = natural_position.pop(0)

            if key in used_keys:
                continue

            result.append((key, entries[key]))
            used_keys.append(key)
            position = position + 1

        return result

    def compute_used_items_score(self, entries, commands_performed):

        # a list with the keys of used entries, separated by space
        used_items = commands_performed["key"].tolist()

        # linear decay for use
        total_used_items = len(used_items)
        scores_used_items = {}
        for position, key in enumerate(used_items):
            if key not in entries:
                logger.info(f"key not in entries: {key}")
                continue

            score = (total_used_items - position) / total_used_items

            if key in scores_used_items:
                aggregation = score + (scores_used_items[key] * (1 / position))
                score = aggregation if aggregation < 1 else 1

            scores_used_items[key] = score
        used_items = sorted(scores_used_items, key=scores_used_items.get, reverse=True)

        return used_items

    def compute_natural_position_scores(self, entries):
        # quadratic decay for position
        total_items = len(entries)
        natural_position_scored = {}
        for position, (key, value) in enumerate(entries.items()):

            natural_position_scored[key] = total_items / (total_items + position)

        natural_position = sorted(
            natural_position_scored, key=natural_position_scored.get, reverse=True
        )

        return natural_position

    def load_commands_performed_df(self):
        with open("/data/grimoire/message_topics/run_key_command_performed") as f:
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

    def _export_to_file(self, data):
        fzf_lines = ""
        for name, content in data:
            fzf_lines += f"{name.lower()}: {content}\n"

        write_file(self.configuration.cached_filename, fzf_lines)
