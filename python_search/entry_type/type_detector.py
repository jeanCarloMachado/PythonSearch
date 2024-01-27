from typing import Literal


class TypeDetector:
    classifier = None

    def __init__(self):
        from python_search.ps_llm.tasks.classity_entry_type import ClassifyEntryType
        from python_search.configuration.loader import ConfigurationLoader

    def detect(self, key, content) -> Literal["Url", "Snippet", "File", "Cmd"]:
        if content.startswith("https://") or content.startswith("http://"):
            return "Url"
        return "Snippet"
