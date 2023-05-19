from typing import List


def prepend_order_in_entries(entries: List[str]) -> List[str]:
    order = 1
    for entry in entries:
        entry = f"{order}. {entry}"
        order += 1
        yield entry
