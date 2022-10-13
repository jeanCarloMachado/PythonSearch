import os


class Context:
    """
    captures information from the environment
    to contextualize how to execute the command
    """

    _instance = None
    _is_cli: bool = False
    _is_group_command = False
    _should_execute_sequentially = False
    _input = None

    @staticmethod
    def get_instance():
        if not Context._instance:
            Context._instance = Context()

        return Context._instance

    def is_cli(self):
        if os.environ.get("DISABLE_CLI"):
            return False

        return self._is_cli

    def enable_gui_mode(self):
        self._is_cli = False
        return self

    def enable_group_command(self):
        self._is_group_command = True
        return self

    def is_group_command(self):
        return self._is_group_command

    def enable_sequential_execution(self):
        self._should_execute_sequentially = True

    def disable_sequential_execution(self):
        self._should_execute_sequentially = False

    def should_execute_sequentially(self):
        return self._should_execute_sequentially

    def set_interpreter(self, interpreter):
        self._interpreter = interpreter

    def get_interpreter(self):
        return self._interpreter

    def set_input(self, input):
        self._input = input

    def get_input(self):
        return self._input
