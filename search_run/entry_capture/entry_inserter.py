from __future__ import annotations

from datetime import datetime

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
        self.file_to_append = self.configuration.get_project_root() + "/entries/main.py"

    def insert(self, key: str, entry: dict):

        entry["created_at"] = datetime.now().isoformat()

        try:

            row_entry = str(entry)
            line_to_add = f"    '{key}': {row_entry},"
            self.append_entry(line_to_add)
        except Exception as e:
            send_notification(f"Error while inserting entry: {e}")
        send_notification(f"Entry {row_entry} inserted successfully")
        # refresh the configuration
        Terminal.run_command("search_run export_configuration")

    def append_entry(self, line_to_add: str):
        with open(self.file_to_append, 'w') as out, open(self.file_to_append) as f:
            for line in f:
                out.write(line)
                if self.NEW_ENTRIES_STRING in line:
                    # insert text.
                    out.write('\n'.join(line_to_add) + '\n')
