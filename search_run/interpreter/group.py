from search_run.context import Context
from search_run.interpreter.base import (
    BaseInterpreter,
)
from search_run.exceptions import CommandDoNotMatchException


class GroupInterpreter(BaseInterpreter):
    def __init__(self, cmd, context: Context):
        self.context = context
        self.cmd = {}

        if type(cmd) is dict and "members" in cmd:
            if cmd["members"] is dict:
                raise Exception(
                    f"Members as dict are no longer valid, use list instead"
                )

            self.cmd["members"] = cmd["members"]
            self.context.enable_group_command()
            if "sequential" in cmd:
                self.context.enable_sequential_execution()

            return

        raise CommandDoNotMatchException(f"Not Valid members command {cmd}")

    def interpret_default(self):
        for member_key in self.cmd["members"]:
            self.context.get_interpreter().default(member_key)

        return
