from python_search.configuration.loader import ConfigurationLoader
from python_search.apps.clipboard import Clipboard
from python_search.core_entities.core_entities import Entry, Key
from python_search.error.exception import notify_exception


class ShareEntry:
    def __init__(self):
        self._entries = ConfigurationLoader().load_entries()

    @notify_exception()
    def share_key(self, key: str):
        """
        deprecated name
        """
        key = str(Key.from_fzf(key))
        if key not in self._entries:
            raise Exception(f"Entry {key} not found")

        entry = Entry(key, self._entries[key])
        result = f"{entry.key}: {entry.get_content_str()}"

        Clipboard().set_content(result, enable_notifications=True, notify=True)

        return result

    def share_only_key(self, key):
        key = str(Key.from_fzf(key))
        Clipboard().set_content(key, enable_notifications=True, notify=True)

    def share_only_value(self, key: str):
        """
        deprecated name
        """
        key = str(Key.from_fzf(key))
        if key not in self._entries:
            raise Exception(f"Entry {key} not found")

        entry = Entry(key, self._entries[key])
        result = f"{entry.get_content_str()}"

        Clipboard().set_content(result, enable_notifications=True, notify=True)

        return result

    def share_entry(self, key):
        self.share_key(key)


def main():
    import fire

    fire.Fire(ShareEntry)


if __name__ == "__main__":
    main()
