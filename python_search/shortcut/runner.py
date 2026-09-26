from __future__ import annotations

from python_search.configuration.loader import ConfigurationLoader
from python_search.entry_runner import EntryRunner
from python_search.shortcut.shortcuts import entry_shortcuts


class ShortcutRunner:
    def __init__(self, configuration=None):
        if not configuration:
            configuration = ConfigurationLoader().load_config()
        self._configuration = configuration
        self._entry_runner = EntryRunner(configuration)

    def run(self, shortcut_pattern: str):
        key = self._find_key_by_shortcut(shortcut_pattern)
        return self._entry_runner.run(key, from_shortcut=True)

    def _find_key_by_shortcut(self, shortcut_pattern: str) -> str:
        normalized_shortcut = self._normalize_shortcut(shortcut_pattern)

        for key, content in self._configuration.commands.items():
            if not isinstance(content, dict):
                continue

            for configured_shortcut in entry_shortcuts(content):
                if self._normalize_shortcut(configured_shortcut) == normalized_shortcut:
                    return key

        raise Exception(f"No key found for shortcut pattern: {shortcut_pattern}")

    @staticmethod
    def _normalize_shortcut(shortcut: str) -> str:
        return "".join(str(shortcut).split()).lower()


def main():
    import fire

    fire.Fire(ShortcutRunner().run)
