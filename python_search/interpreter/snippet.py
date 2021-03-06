from grimoire.shell import shell

from python_search.apps.clipboard import Clipboard
from python_search.exceptions import CommandDoNotMatchException
from python_search.interpreter.base import BaseEntry


class SnippetInterpreter(BaseEntry):
    """
    Snippet handler
    @todo rename to entry.Snippet
    """

    def __init__(self, cmd, context):
        self.context = context

        if type(cmd) is dict and "snippet" in cmd:
            self.cmd = cmd
            return

        raise CommandDoNotMatchException(
            f"Not Valid {self.__class__.__name__} command {cmd}"
        )

    def interpret_default(self):
        Clipboard().set_content(self.cmd["snippet"])

        if "type-it" in self.cmd:
            snippet = self.apply_directory(self.cmd["snippet"])
            shell.run(f"setxkbmap ; xdotool type '{snippet}'")
            shell.run(f"xdotool key Return ")

        return

    def copiable_part(self):
        return self.cmd["snippet"]
