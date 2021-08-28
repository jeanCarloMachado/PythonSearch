from typing import List, Any
from search_run.logger import configure_logger

logger = configure_logger()


class CiclicalPlacement:
    def cyclical_placment(self, entries, commands_performed) -> List[Any]:
        """Put 1 result of natural rank after 1 result of visits"""

        used_items = self.compute_used_items_score(entries, commands_performed)
        natural_position = self.compute_natural_position_scores(entries)

        result = []
        used_keys = []
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
