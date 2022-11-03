from python_search.apps.clipboard import Clipboard
from python_search.exceptions import CommandDoNotMatchException
from python_search.interpreter.base import BaseInterpreter


class SnippetInterpreter(BaseInterpreter):
    """
    Snippet handler
    @todo rename to entry.Snippet
    """

    def __init__(self, cmd, context=None):
        self.context = context

        if type(cmd) == str:
            self.cmd = {"snippet": cmd}
            return

        if type(cmd) is dict and "snippet" in cmd:
            self.cmd = cmd
            return

        raise CommandDoNotMatchException(
            f"Not Valid {self.__class__.__name__} command {cmd}"
        )

    def interpret_default(self):
        Clipboard().set_content(self.cmd["snippet"])
        return

    def copiable_part(self):
        return self.cmd["snippet"]
