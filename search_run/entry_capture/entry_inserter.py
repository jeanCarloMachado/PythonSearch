from __future__ import annotations

from datetime import datetime

from grimoire.file import Replace

from search_run.apps.notification_ui import send_notification
from search_run.apps.terminal import Terminal


class EntryInserter:
    """Add an entry dict to the entries repository"""

    ALLOWED_SPECIAL_CHARS = [
        "@",
        "#",
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

        entry["created_at"] = datetime.now().isoformat()

        try:

            row_entry = str(entry)
            line_to_add = f"    '{key}': {row_entry},"
            Replace().append_after_placeholder(
                # @todo make this not static
                self.configuration.get_project_root() + "/entries/main.py",
                EntryInserter.NEW_ENTRIES_STRING,
                line_to_add,
            )
        except Exception as e:
            send_notification(f"Error while inserting entry: {e}")
        send_notification(f"Entry {row_entry} inserted successfully")
        # refresh the configuration
        Terminal.run_command("search_run export_configuration")
