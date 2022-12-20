from __future__ import annotations

import shutil
from datetime import datetime

from python_search.config import PythonSearchConfiguration
from python_search.events.run_performed import RunPerformed


class FilesystemEntryInserter:
    """
    Class responsible to the actual writing of the new entry in the filesystem
    """

    NEW_ENTRIES_STRING = "# NEW_ENTRIES_HERE"

    def __init__(self, configuration: PythonSearchConfiguration):
        self._configuration = configuration
        self._file_to_append = (
            self._configuration.get_project_root() + "/entries_main.py"
        )
        self._new_entries_string = FilesystemEntryInserter.NEW_ENTRIES_STRING

    def insert(self, key: str, entry: dict):

        entry["created_at"] = datetime.now().isoformat()

        if "tags" in entry and self._configuration.tags_dependent_inserter_marks:
            for tag in entry["tags"]:
                if tag in self._configuration.tags_dependent_inserter_marks.keys():
                    self._new_entries_string = (
                        self._configuration.tags_dependent_inserter_marks[tag][0]
                    )
                    self._file_to_append = (
                        self._configuration.get_project_root()
                        + "/"
                        + self._configuration.tags_dependent_inserter_marks[tag][1]
                    )

        row_entry = str(entry)
        line_to_add = f"    '{key}': {row_entry},"
        self._append_entry(line_to_add)

        from python_search.events.run_performed.writer import LogRunPerformedClient
        LogRunPerformedClient().send(
            RunPerformed(key=key, query_input="", shortcut=False)
        )

        from python_search.apps.notification_ui import send_notification

        send_notification(f"Entry {row_entry} inserted successfully")

    def _append_entry(self, line_to_add: str):
        """
        This script does the following:
            Copies the main file,
            add the new entry to it
            Compile to see if it is still valid python
            If so, then replaces it
        """
        copy_file = self._file_to_append + "cpy"

        print(f"Copying file as backup {self._file_to_append} => {copy_file}")
        shutil.copyfile(self._file_to_append, copy_file)

        with open(copy_file, "w") as out, open(self._file_to_append) as source_file:
            for line in source_file:
                out.write(line)
                if self._new_entries_string in line:
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

        shutil.move(copy_file, self._file_to_append)
