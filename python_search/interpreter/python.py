from python_search.exceptions import CommandDoNotMatchException
from python_search.interpreter.base import BaseInterpreter


class PythonInterpreter(BaseInterpreter):
    def __init__(self, cmd, context=None):

        self.context = context

        if type(cmd) is dict and "callable" in cmd:
            self.cmd = cmd
            return

        raise CommandDoNotMatchException(f"Not Valid Python command {cmd}")

    def interpret_default(self):
        return self.cmd["callable"]

    def serialize(self):
        import dill

        return dill.source.getsource(self.cmd["callable"])
