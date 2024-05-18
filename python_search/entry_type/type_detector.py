from typing import Literal


class TypeDetector:
    classifier = None

    def __init__(self):
        pass

    def detect(self, key, content) -> Literal["Url", "Snippet", "File", "Cmd"]:
        if content.startswith("https://") or content.startswith("http://"):
            return "Url"
        return "Snippet"
