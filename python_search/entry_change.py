from typing import List

from python_search.configuration.loader import ConfigurationLoader


class EntryChangeDetector:

    HASH_FILE = "/tmp/entries_md5"

    def has_changed(self) -> bool:
        result = self.current_entries_md5() != self.previous_entries_md5()

        if result:
            self.save_current_entries_md5()
        return result

    def previous_entries_md5(self) -> str:
        try:
            with open(self.HASH_FILE, "r") as file:
                return file.read()
        except FileNotFoundError:
            return ""

    def save_current_entries_md5(self) -> None:
        with open(self.HASH_FILE, "w") as file:
            file.write(self.current_entries_md5())

    def current_entries_md5(self) -> str:
        import hashlib

        self.commands = ConfigurationLoader().load_config().commands
        self.entries: List[str] = list(self.commands.keys())

        # md5 call
        result = hashlib.md5(str(self.entries).encode())
        return result.hexdigest()


if __name__ == "__main__":
    import fire

    fire.Fire(EntryChangeDetector)
