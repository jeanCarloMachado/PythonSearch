from python_search.host_system.system_paths import SystemPaths


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

        result = ""

        try:
            import subprocess

            output = subprocess.getoutput(
                SystemPaths.BINARIES_PATH + "/pys _entries_loader load_entries_as_json"
            )
            result = hashlib.md5(output.encode())
            result = result.hexdigest()
        except Exception:
            pass

        return result


if __name__ == "__main__":
    import fire

    fire.Fire(EntryChangeDetector)
