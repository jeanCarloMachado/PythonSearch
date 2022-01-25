from __future__ import annotations

from grimoire.file import Replace

from search_run.apps.terminal import Terminal
from search_run.observability.logger import logging


class EntryInserter:
    """ Add an entry to the repository """

    ALLOWED_SPECIAL_CHARS = [
        "@",
        "-",
        "_",
        "'",
        "?",
        "=",
        ",",
        ".",
        " ",
        "/",
        "(",
        ")",
        ";",
        '"',
        "%",
        " ",
        ":",
        "{",
        "'",
        '"',
        "}",
        "?",
    ]
    NEW_ENTRIES_STRING = "# NEW_ENTRIES_HERE"

    def __init__(self, configuration):
        self.configuration = configuration

    def insert(self, key: str, entry: dict):

        row_entry = str(entry)
        line_to_add = f"    '{key}': {row_entry},"
        Replace().append_after_placeholder(
            # @todo make this not static
            self.configuration.get_project_root() + "/entries/main.py",
            EntryInserter.NEW_ENTRIES_STRING,
            line_to_add,
        )

        logging.info(f"Inserting line: '{line_to_add}'")
        # refresh the configuration
        Terminal.run_command("search_run export_configuration")
