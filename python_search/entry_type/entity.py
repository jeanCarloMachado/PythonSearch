from __future__ import annotations

from enum import Enum

from python_search.interpreter.file import FileInterpreter
from python_search.interpreter.url import UrlInterpreter


class EntryType(str, Enum):
    URL = "Url"
    FILE = "File"
    CMD = "Cmd"
    SNIPPET = "Snippet"
    CALLABLE = "Callable"

    @staticmethod
    def all():
        return {
            0: EntryType.URL,
            1: EntryType.SNIPPET,
            2: EntryType.CMD,
            3: EntryType.FILE,
            4: EntryType.CALLABLE,
        }

    @staticmethod
    def from_categorical(categorical: int) -> "EntryType":
        return EntryType.all()[categorical]

    @staticmethod
    def to_categorical(type: "EntryType") -> int:
        """
        @ todo see if we can use self for this function instead, how does it work with enums?

        :param type:
        :return:
        """
        all = list(EntryType.all().values())

        return all.index(type)


def infer_default_type(content: str) -> EntryType:

    if False:
        from python_search.entry_type.classifier_inference import predict_entry_type
        return predict_entry_type(content)


    if UrlInterpreter.is_url(content):
        return EntryType.URL

    if FileInterpreter.file_exists(content):
        return EntryType.FILE

    return EntryType.SNIPPET
