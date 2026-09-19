import json
import os
import time
from typing import List

from python_search.configuration.loader import ConfigurationLoader
from python_search.core_entities import Entry


class EntriesLoader:
    """Class to access the current existing key"""

    @staticmethod
    def count_entries_from_disk() -> int:
        """
        Reload ``entries_main`` from disk and return how many keys exist in ``config.commands``.
        Same source as the Search UI (``load_entries_as_json`` / ``load_only_keys``).
        """
        ConfigurationLoader().reload()
        return len(ConfigurationLoader().load_entries())

    @staticmethod
    def load_only_keys() -> List[str]:
        """
        Return just the key names strings
        """
        keys = list(ConfigurationLoader().load_entries().keys())

        print("Loaded in total " + str(len(keys)) + " keys")

        return keys

    def load_entries(self) -> dict:
        return EntriesLoader.load_all_entries()

    def load_entries_as_json(self):
        import json

        result = {}
        for entry in EntriesLoader.load_all_entries():
            result[entry.key] = entry.get_serialized_value()

        return json.dumps(result)

    # Fields copied verbatim into the rich dump consumed by the Rust launcher.
    DUMP_PASSTHROUGH_FIELDS = (
        "tags",
        "created_at",
        "description",
        "mac_shortcut",
        "mac_shortcuts",
        "app_mode",
        "focus_match",
        "app_focus_title",
        "directory",
        "browser",
        "new-window-non-cli",
    )

    DEFAULT_DUMP_PATH = os.path.expanduser("~/.python_search/data/entries.json")

    @staticmethod
    def dump_entries(path: str = None) -> str:
        """
        Write a rich, machine readable dump of all entries for external consumers (the Rust launcher).

        Unlike load_entries_as_json this keeps the full attribute bag, not only the type and content.
        The write is atomic so a reader never observes a partial file.
        """
        path = path or EntriesLoader.DEFAULT_DUMP_PATH
        entries = ConfigurationLoader().load_entries()

        records = []
        for key, value in entries.items():
            entry = Entry(key, value)
            record = {
                "key": key,
                "type": entry.get_type_str(),
                "content": entry.get_content_str(strip_new_lines=True),
            }
            if isinstance(value, dict):
                for field in EntriesLoader.DUMP_PASSTHROUGH_FIELDS:
                    if field in value:
                        record[field.replace("-", "_")] = EntriesLoader._jsonable(value[field])
            records.append(record)

        os.makedirs(os.path.dirname(path), exist_ok=True)
        tmp_path = f"{path}.tmp.{os.getpid()}"
        with open(tmp_path, "w") as f:
            json.dump(records, f, ensure_ascii=False)
        os.replace(tmp_path, path)

        EntriesLoader._write_dump_metadata(path)

        print(f"Dumped {len(records)} entries to {path}")
        return path

    @staticmethod
    def _jsonable(value):
        """Keep JSON native values as they are, stringify anything else (callables, class objects)."""
        if value is None or isinstance(value, (bool, int, float, str)):
            return value
        if isinstance(value, (list, tuple)):
            return [EntriesLoader._jsonable(item) for item in value]
        if isinstance(value, dict):
            return {str(k): EntriesLoader._jsonable(v) for k, v in value.items()}
        return str(value)

    @staticmethod
    def _write_dump_metadata(dump_path: str) -> None:
        """
        Record the newest mtime across the entries sources so a reader can tell whether the dump is stale.
        """
        root = os.path.abspath(ConfigurationLoader().get_entries_project_root())
        newest = 0.0
        for source in EntriesLoader.entries_source_files(root):
            try:
                newest = max(newest, os.path.getmtime(source))
            except OSError:
                continue

        metadata = {
            "entries_project_root": root,
            "newest_source_mtime": newest,
            "dumped_at": time.time(),
        }
        with open(f"{dump_path}.meta", "w") as f:
            json.dump(metadata, f)

    @staticmethod
    def entries_source_files(root: str = None):
        """Every Python file the entries database is built from."""
        root = root or os.path.abspath(ConfigurationLoader().get_entries_project_root())
        main = os.path.join(root, "entries_main.py")
        if os.path.exists(main):
            yield main
        for folder, _, filenames in os.walk(os.path.join(root, "entries")):
            if "__pycache__" in folder:
                continue
            for filename in filenames:
                if filename.endswith(".py"):
                    yield os.path.join(folder, filename)

    @staticmethod
    def load_all_entries() -> List[Entry]:
        """
        Return just the key names strings
        """

        entries = ConfigurationLoader().load_entries()
        return EntriesLoader.convert_to_list_of_entries(entries)

    @staticmethod
    def convert_to_list_of_entries(entries: dict) -> List[Entry]:
        for key, value in entries.items():
            yield Entry(key, value)


if __name__ == "__main__":
    import fire

    fire.Fire(EntriesLoader)
