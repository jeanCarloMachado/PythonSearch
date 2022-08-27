from __future__ import annotations

import shutil
from datetime import datetime

from python_search.config import PythonSearchConfiguration


class EntryInserter:
    """
    Class responsible to the actual writing of the new entry
    """

    NEW_ENTRIES_STRING = "# NEW_ENTRIES_HERE"

    def __init__(self, configuration: PythonSearchConfiguration):
        self.configuration = configuration
        self.file_to_append = self.configuration.get_project_root() + "/entries_main.py"

    def insert(self, key: str, entry: dict, enable_shortcuts_generation=False):

        entry["created_at"] = datetime.now().isoformat()

        row_entry = str(entry)
        line_to_add = f"    '{key}': {row_entry},"
        self._append_entry(line_to_add)

        if self.configuration.supported_features.is_enabled("event_tracking"):
            from python_search.events.events import SearchRunPerformed
            from python_search.events.producer import EventProducer

            EventProducer().send_object(
                SearchRunPerformed(key=key, query_input="", shortcut=False)
            )

        from python_search.apps.notification_ui import send_notification

        send_notification(f"Entry {row_entry} inserted successfully")

        # refresh the configuration
        if enable_shortcuts_generation:
            from python_search.interpreter.cmd import CmdInterpreter

            CmdInterpreter({"cmd": "python_search generate_shortcuts"})

    def _append_entry(self, line_to_add: str):
        """
        This script does the following:
            Copies the main file,
            add the new entry to it
            Compile to see if it is still valid python
            If so, then replaces it
        """
        copy_file = self.file_to_append + "cpy"

        shutil.copyfile(self.file_to_append, copy_file)

        with open(copy_file, "w") as out, open(self.file_to_append) as source_file:
            for line in source_file:
                out.write(line)
                if self.NEW_ENTRIES_STRING in line:
                    # insert text.
                    print(f"Writing line: {line_to_add}")
                    out.write(line_to_add + "\n")

        # compile and make sure the file is a valid python
        import os

        if os.system(f"python3 -m compileall -q {copy_file}") != 0:
            message = "Copy of file does not compile so wont proceed replacing!"
            from python_search.apps.notification_ui import send_notification

            send_notification(message)
            raise Exception(message)

        shutil.move(copy_file, self.file_to_append)
