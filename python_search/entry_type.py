from __future__ import annotations

from python_search.interpreter.file import FileInterpreter
from python_search.interpreter.url import UrlInterpreter
from enum import Enum

class EntryType(str, Enum):
    URL = "Url"
    FILE = "File"
    CMD = "Cmd"
    SNIPPET = "Snippet"
    CALLABLE = "Callable"

    @staticmethod
    def all():
        return [EntryType.URL, EntryType.SNIPPET, EntryType.CMD, EntryType.FILE, EntryType.CALLABLE]

    @staticmethod
    def to_categorical(type: "EntryType") -> int:
        """
        @ todo see if we can use self for this function instead, how does it work with enums?

        :param type:
        :return:
        """
        all = EntryType.all()

        return all.index(type)


def infer_default_type(content: str) -> EntryType:
    if UrlInterpreter.is_url(content):
        return EntryType.URL

    if FileInterpreter.file_exists(content):
        return EntryType.FILE

    return EntryType.SNIPPET


if __name__ == '__main__':
    import fire
    fire.Fire()
